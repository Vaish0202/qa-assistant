"""
Convert the data we already have into the v1 format.

  - sample_data/test_cases.py (30 hand-written cases)  -> source "legacy_sample"
  - dataset.json from fetch.py (Stack Overflow)         -> source "stackoverflow"
    Only entries that have a label AND a log are kept.

Usage (from the project root):
    python -m evaluation.datasets.convert_existing
    python -m evaluation.datasets.convert_existing --so dataset.json

Writes evaluation/datasets/v1.jsonl. If v1.jsonl already exists, records
with the same id keep their existing split, so re-running never moves a
test case into dev.
"""
import argparse
import contextlib
import io as _io
import json
import os
import re

from agents.framework_detector import detect_framework
from evaluation.datasets import dataset_io
from evaluation.datasets.schema import DETECTOR_TO_DATASET, LABELS

# Lines that belong to a stack trace rather than the error message.
STACK_LINE = re.compile(
    r"^\s*(Traceback \(most recent call last\)|File \".*\", line \d+|at [\w$.<>]+\(.*\)"
    r"|at .+:\d+(:\d+)?\)?$|Stacktrace:|#\d+ 0x[0-9a-f]+|\.\.\. \d+ more)",
    re.IGNORECASE,
)


def split_log_and_stacktrace(text: str):
    log_lines, stack_lines = [], []
    for line in (text or "").strip("\n").splitlines():
        (stack_lines if STACK_LINE.match(line) else log_lines).append(line)
    return "\n".join(log_lines).strip(), "\n".join(stack_lines).strip()


def framework_for(logs: str, code: str, description: str) -> str:
    with contextlib.redirect_stdout(_io.StringIO()):   # detector prints a line
        detected = detect_framework(logs, code, description)["framework"]
    return DETECTOR_TO_DATASET.get(detected, "unit")


def make_record(rid, logs, code, description, label, source, source_ref):
    log, stack = split_log_and_stacktrace(logs)
    return {
        "id": rid,
        "framework": framework_for(logs, code, description),
        "log": log,
        "stacktrace": stack,
        "code_snippet": (code or "").strip("\n"),
        "description": (description or "").strip(),
        "label": label,
        "source": source,
        "source_ref": source_ref,
        "split": "",
    }


def from_legacy():
    from sample_data.test_cases import TEST_CASES
    return [make_record(f"legacy-{tc['id']}", tc["testcase_logs"], tc["testcase_code"],
                        tc["testcase_description"], tc["expected"],
                        "legacy_sample", "sample_data/test_cases.py")
            for tc in TEST_CASES]


def from_stackoverflow(path):
    with open(path, encoding="utf-8") as f:
        entries = json.load(f)
    kept, skipped = [], {"no_label": 0, "no_log": 0}
    for e in entries:
        label = (e.get("label") or "").strip()
        if label not in LABELS:
            skipped["no_label"] += 1
            continue
        if not (e.get("logs") or "").strip():
            skipped["no_log"] += 1
            continue
        qid = e.get("source", "").rstrip("/").split("/")[-1]
        kept.append(make_record(f"so-{qid}", e["logs"], e.get("code", ""),
                                e.get("description", ""), label,
                                "stackoverflow", "https://" + e.get("source", "")))
    print(f"Stack Overflow: kept {len(kept)}, skipped {skipped['no_label']} "
          f"without a label and {skipped['no_log']} without a log")
    return kept


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--so", help="path to dataset.json from fetch.py")
    ap.add_argument("--out", default="v1")
    args = ap.parse_args()

    records = from_legacy()
    print(f"Legacy sample cases: {len(records)}")
    if args.so:
        records += from_stackoverflow(args.so)

    # Keep records and splits that are already in the file.
    existing = {}
    if os.path.exists(dataset_io.dataset_path(args.out)):
        existing = {r["id"]: r for r in dataset_io.load(args.out)}
    merged = dict(existing)
    for r in records:
        if r["id"] in existing:
            r["split"] = existing[r["id"]].get("split", "")
        merged[r["id"]] = r

    path = dataset_io.save(args.out, list(merged.values()))
    print(f"Wrote {len(merged)} records to {path}")
    print("Next: python -m evaluation.datasets.validate --dataset v1")


if __name__ == "__main__":
    main()