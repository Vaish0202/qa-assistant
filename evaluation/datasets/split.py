"""
Assign an 80/20 dev/test split, stratified by framework and label.

Rules:
  - Records that already have a split keep it. Running this again after
    adding new cases only splits the new ones, so the test set never loses
    or swaps cases.
  - legacy_sample cases always go to dev (they shaped the prompts).
  - Fixed random seed, so the same file always gives the same split.
  - Writes vN.manifest.json with the test ids; validate.py fails if they
    change later.
  - synthetic cases are split by template: one whole template per
    framework x label goes to test, so test templates are never seen in dev.
    
Use dev for anything you tune (prompts, features, thresholds). Use test
only for final numbers.

Usage:
    python -m evaluation.datasets.split --dataset v1
"""
import argparse
import hashlib
import json
import os
import random
import sys
from collections import Counter, defaultdict

from evaluation.datasets import dataset_io
from evaluation.datasets.validate import manifest_path

TEST_FRACTION = 0.2
SEED = 42

# The 30 legacy sample cases were used while writing the prompts and
# features, so they are not unseen data. They always go to dev.
DEV_ONLY_SOURCES = {"legacy_sample"}
TEMPLATE_SOURCES = {"synthetic"}

def assign(records, test_fraction=TEST_FRACTION, seed=SEED):
    strata = defaultdict(list)
    for r in records:
        if r["source"] in DEV_ONLY_SOURCES:
            if not r.get("split"):
                r["split"] = "dev"
            continue
        strata[(r["framework"], r["label"])].append(r)

    rng = random.Random(seed)
    for key in sorted(strata):
        group = strata[key]
        synthetic = [r for r in group if r["source"] in TEMPLATE_SOURCES]
        real = [r for r in group if r["source"] not in TEMPLATE_SOURCES]
        _assign_by_template(synthetic, rng)
        _assign_rows(real, test_fraction, rng)
    return records


def _assign_rows(group, test_fraction, rng):
    """Real cases: pick individual cases for test."""
    already_test = sum(1 for r in group if r.get("split") == "test")
    new = sorted((r for r in group if not r.get("split")), key=lambda r: r["id"])
    rng.shuffle(new)
    # How many test cases this stratum should have in total, minus those it has.
    target_test = round(len(group) * test_fraction)
    need = max(0, target_test - already_test)
    for i, r in enumerate(new):
        r["split"] = "test" if i < need else "dev"


def _assign_by_template(group, rng):
    """Synthetic cases: hold out whole templates.

    Cases made from the same template look alike. If one went to dev and
    its twin to test, a model would only have to remember the template.
    So every template goes entirely to dev or entirely to test, and each
    stratum keeps one template (with all its cases) for test only.
    """
    by_template = defaultdict(list)
    for r in group:
        by_template[r["source_ref"]].append(r)
    if not by_template:
        return
    # A template that already has a split keeps it for any new cases.
    decided = {}
    for ref, cases in by_template.items():
        splits = {r["split"] for r in cases if r.get("split")}
        if splits:
            decided[ref] = "test" if "test" in splits else "dev"
    if len(by_template) > 1 and "test" not in decided.values():
        undecided = sorted(ref for ref in by_template if ref not in decided)
        if undecided:
            decided[rng.choice(undecided)] = "test"
    for ref, cases in by_template.items():
        for r in cases:
            if not r.get("split"):
                r["split"] = decided.get(ref, "dev")


def write_manifest(name, records):
    test_ids = sorted(r["id"] for r in records if r["split"] == "test")
    manifest = {
        "dataset": name,
        "seed": SEED,
        "test_fraction": TEST_FRACTION,
        "n_records": len(records),
        "split_counts": dict(Counter(r["split"] for r in records)),
        "test_ids": test_ids,
        "test_ids_sha256": hashlib.sha256("\n".join(test_ids).encode()).hexdigest(),
    }
    with open(manifest_path(name), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="v1")
    name = ap.parse_args().dataset

    records = dataset_io.load(name)

    # Refuse to re-freeze if someone moved a frozen test case out of test.
    if os.path.exists(manifest_path(name)):
        with open(manifest_path(name), encoding="utf-8") as f:
            frozen = set(json.load(f)["test_ids"])
        now_test = {r["id"] for r in records if r.get("split") == "test"}
        lost = sorted(frozen - now_test)
        if lost:
            sys.exit(f"These frozen test cases are no longer in test: {lost[:10]}\n"
                     f"Put them back (split='test') instead of re-splitting.")

    records = assign(records)
    dataset_io.save(name, records)
    m = write_manifest(name, records)

    print(f"Split {m['n_records']} records: {m['split_counts']}")
    counts = Counter((r["framework"], r["label"], r["split"]) for r in records)
    for (fw, lb) in sorted({(fw, lb) for fw, lb, _ in counts}):
        print(f"  {fw:11s} {lb:16s} dev={counts[(fw, lb, 'dev')]:3d} "
              f"test={counts[(fw, lb, 'test')]:3d}")
    print(f"Froze test ids in {manifest_path(name)}")


if __name__ == "__main__":
    main()