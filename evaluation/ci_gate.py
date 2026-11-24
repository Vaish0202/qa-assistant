"""
CI regression gate: fail the build if classification quality drops.

Runs the XGBoost pipeline on the frozen test split (fast, deterministic, no
LLM, no network) and compares macro-F1 with evaluation/baseline.json.

    python -m evaluation.ci_gate                    # check (used in CI)
    python -m evaluation.ci_gate --update-baseline  # after an intended change

Fails (exit code 1) when:
  - macro-F1 dropped more than MAX_DROP (3 points) below the baseline, or
  - the test split changed since the baseline was recorded (test ids hash
    differs), because then the numbers aren't comparable.
Improvements pass; update the baseline on purpose to lock them in.
"""
import argparse
import json
import os
import sys

from evaluation.datasets import dataset_io
from evaluation.datasets.validate import manifest_path
from evaluation.metrices import classification_metrics
from evaluation.predictors import predict_xgboost

BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "baseline.json")
MAX_DROP = 0.03


def current_scores(dataset: str) -> dict:
    records = dataset_io.load(dataset, split="test")
    y_true = [r["label"] for r in records]
    y_pred = [predict_xgboost(r)["pred"] for r in records]
    m = classification_metrics(y_true, y_pred)
    with open(manifest_path(dataset), encoding="utf-8") as f:
        test_hash = json.load(f)["test_ids_sha256"]
    return {"dataset": dataset, "pipeline": "xgboost", "n": m["n"],
            "accuracy": round(m["accuracy"], 4), "macro_f1": round(m["macro_f1"], 4),
            "test_ids_sha256": test_hash}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="v1")
    ap.add_argument("--update-baseline", action="store_true")
    args = ap.parse_args()

    now = current_scores(args.dataset)
    print(f"Current:  macro-F1 {now['macro_f1']:.3f}  accuracy {now['accuracy']:.3f}  "
          f"(xgboost, {args.dataset} test split, n={now['n']})")

    if args.update_baseline:
        with open(BASELINE, "w", encoding="utf-8") as f:
            json.dump(now, f, indent=2)
        print(f"Baseline written to {BASELINE}. Commit it.")
        return

    if not os.path.exists(BASELINE):
        sys.exit("No baseline yet. Run: python -m evaluation.ci_gate --update-baseline")
    with open(BASELINE, encoding="utf-8") as f:
        base = json.load(f)
    print(f"Baseline: macro-F1 {base['macro_f1']:.3f}  accuracy {base['accuracy']:.3f}")

    if base.get("test_ids_sha256") != now["test_ids_sha256"]:
        sys.exit("FAIL: the test split changed since the baseline was recorded, so the "
                 "scores are not comparable. If that was intended, run "
                 "--update-baseline and commit baseline.json.")

    drop = base["macro_f1"] - now["macro_f1"]
    if drop > MAX_DROP:
        sys.exit(f"FAIL: macro-F1 dropped {drop * 100:.1f} points "
                 f"(allowed: {MAX_DROP * 100:.0f}).")
    change = round((now["macro_f1"] - base["macro_f1"]) * 100, 1) + 0.0   # avoid "-0.0"
    print(f"PASS: macro-F1 change {change:+.1f} points (allowed drop: {MAX_DROP * 100:.0f}).")


if __name__ == "__main__":
    main()