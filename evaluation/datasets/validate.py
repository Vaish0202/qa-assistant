"""
Check a dataset file before using it.

Errors (exit code 1): missing fields, bad label/framework/source/split,
duplicate ids, exact duplicate cases, test ids changed since the split was
frozen.
Warnings: empty logs/code, near-copies of the XGBoost training examples
(the model has effectively seen those), strata too small to measure.

Usage:
    python -m evaluation.datasets.validate --dataset v1
"""
import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter

from evaluation.datasets import dataset_io
from evaluation.datasets.schema import (FRAMEWORKS, LABELS, REQUIRED_FIELDS,
                                        SOURCES, SPLITS)

NEAR_COPY_THRESHOLD = 0.8      # token-set Jaccard similarity
MIN_PER_STRATUM = 15           # target per framework x label


def tokens(text: str) -> set:
    return set(re.findall(r"[a-z_][a-z0-9_]+|\d+", text.lower()))


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def case_text(log, code):
    return f"{log}\n{code}"


def fingerprint(r) -> str:
    norm = re.sub(r"\s+", " ", case_text(r["log"] + r.get("stacktrace", ""),
                                          r["code_snippet"])).strip().lower()
    return hashlib.sha256(norm.encode()).hexdigest()


def manifest_path(name):
    return dataset_io.dataset_path(name).replace(".jsonl", ".manifest.json")


def validate(name: str) -> int:
    records = dataset_io.load(name)
    errors, warnings = [], []

    # 1. fields and allowed values
    for i, r in enumerate(records, 1):
        rid = r.get("id", f"<line {i}>")
        missing = [f for f in REQUIRED_FIELDS if f not in r]
        if missing:
            errors.append(f"{rid}: missing fields {missing}")
            continue
        for field, allowed in (("label", LABELS), ("framework", FRAMEWORKS),
                               ("source", SOURCES)):
            if r[field] not in allowed:
                errors.append(f"{rid}: {field}={r[field]!r} not in {allowed}")
        if r["split"] not in SPLITS + [""]:
            errors.append(f"{rid}: split={r['split']!r} not in {SPLITS}")
        if not r["log"].strip() and not r["stacktrace"].strip():
            warnings.append(f"{rid}: empty log and stacktrace")
        if not r["code_snippet"].strip():
            warnings.append(f"{rid}: empty code_snippet")
    if errors:
        return report(records, errors, warnings)

    # 2. duplicates
    for rid, n in Counter(r["id"] for r in records).items():
        if n > 1:
            errors.append(f"duplicate id {rid} ({n} times)")
    seen = {}
    for r in records:
        fp = fingerprint(r)
        if fp in seen:
            errors.append(f"{r['id']}: same log+code as {seen[fp]}")
        seen.setdefault(fp, r["id"])

    # 3. near-copies of XGBoost training data
    try:
        from ml_classifier.training_data import TRAINING_DATA
        train = [tokens(case_text(t["logs"], t["code"])) for t in TRAINING_DATA]
        for r in records:
            tk = tokens(case_text(r["log"] + " " + r["stacktrace"], r["code_snippet"]))
            best = max((jaccard(tk, t) for t in train), default=0)
            if best >= NEAR_COPY_THRESHOLD:
                warnings.append(f"{r['id']}: {best:.0%} similar to an XGBoost "
                                f"training example (results on it will look too good)")
    except ImportError:
        warnings.append("could not import ml_classifier.training_data; "
                        "skipped training-overlap check")

    # 4. frozen test split must not change
    mpath = manifest_path(name)
    if os.path.exists(mpath):
        with open(mpath, encoding="utf-8") as f:
            manifest = json.load(f)
        test_ids = sorted(r["id"] for r in records if r["split"] == "test")
        if test_ids != manifest["test_ids"]:
            added = set(test_ids) - set(manifest["test_ids"])
            removed = set(manifest["test_ids"]) - set(test_ids)
            errors.append(f"test split changed since it was frozen "
                          f"(added {sorted(added)[:5]}, removed {sorted(removed)[:5]})")

    # 5. stratum sizes
    counts = Counter((r["framework"], r["label"]) for r in records)
    for fw in FRAMEWORKS:
        for lb in LABELS:
            if counts[(fw, lb)] < MIN_PER_STRATUM:
                warnings.append(f"only {counts[(fw, lb)]} {fw}/{lb} cases "
                                f"(target ≥{MIN_PER_STRATUM})")

    return report(records, errors, warnings)


def report(records, errors, warnings) -> int:
    print(f"\n{len(records)} records\n")
    counts = Counter((r.get("framework"), r.get("label")) for r in records)
    print(f"{'framework':12s} {'bug':>5s} {'failed_tc':>10s} {'total':>6s}")
    for fw in FRAMEWORKS:
        b, f = counts[(fw, "bug")], counts[(fw, "failed_testcase")]
        print(f"{fw:12s} {b:5d} {f:10d} {b + f:6d}")
    print("\nby source:", dict(Counter(r.get("source") for r in records)))
    print("by split: ", dict(Counter(r.get("split") or "(none)" for r in records)))

    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for w in warnings:
            print("  WARN ", w)
    if errors:
        print(f"\n{len(errors)} error(s):")
        for e in errors:
            print("  ERROR", e)
        return 1
    print("\nOK")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="v1")
    sys.exit(validate(ap.parse_args().dataset))


if __name__ == "__main__":
    main()