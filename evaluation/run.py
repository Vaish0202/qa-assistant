"""
Evaluation CLI: score classification pipelines on a dataset split.

Usage (from the project root):
    python -m evaluation.run --dataset v1 --pipeline xgboost
    python -m evaluation.run --dataset v1 --pipeline all
    python -m evaluation.run --dataset v1 --pipeline llm --limit 5      # quick check
    python -m evaluation.run --dataset v1 --pipeline hybrid --split dev --threshold 0.8

--split test (default) is the frozen test split: report these numbers.
--split dev is for choosing settings such as --threshold. Never tune on test.

Writes evaluation/results/run_<date>_<split>/:
    results.json   every number, plus each case's prediction
    report.md      tables for the README
    confusion_<pipeline>.png
"""
import argparse
import json
import os
import time
from collections import Counter

import numpy as np

from evaluation.datasets import dataset_io
from evaluation.metrices import (LABELS, UNPARSED, bootstrap_ci, classification_metrics,
                                confusion, group_metrics, mcnemar_p)
from evaluation.predictors import LLMPredictor, make_hybrid, predict_xgboost

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
ALL_PIPELINES = ["xgboost", "llm", "hybrid"]


# ------------------------------------------------------------ select cases
def select(records, split, limit):
    if split != "all":
        records = [r for r in records if r["split"] == split]
    return records[:limit] if limit else records


# ---------------------------------------------------------------- run one
def run_pipeline(name, predict, records):
    rows = []
    for i, record in enumerate(records, 1):
        res = predict(record)
        rows.append(res)
        if name != "xgboost":                    # LLM is slow: show progress
            mark = "ok" if res["pred"] == record["label"] else ("ERR" if res["error"] else "x")
            cached = " (cached)" if res.get("cached") else ""
            print(f"  [{i}/{len(records)}] {record['id'][:45]:45s} {mark:3s} "
                  f"{res['seconds']:5.1f}s {res['source']}{cached}")
            if res["error"]:
                print(f"      {res['error']}")

    y_true = [r["label"] for r in records]
    y_pred = [x["pred"] or UNPARSED for x in rows]
    return {
        "metrics": classification_metrics(y_true, y_pred),
        "accuracy_ci": bootstrap_ci(y_true, y_pred, "accuracy"),
        "macro_f1_ci": bootstrap_ci(y_true, y_pred, "macro_f1"),
        "confusion": confusion(y_true, y_pred),
        "by_framework": group_metrics(records, y_pred, "framework"),
        "by_source": group_metrics(records, y_pred, "source"),
        "p50_seconds": float(np.median([x["seconds"] for x in rows])),
        "llm_calls": sum(1 for x in rows
                         if x["source"].startswith("llm") and not x.get("cached")),
        "llm_answers_used": sum(1 for x in rows if x["source"].startswith("llm")),
        "unparsed": sum(1 for p in y_pred if p == UNPARSED),
        "predictions": [{"id": r["id"], "true": r["label"], "pred": x["pred"],
                         "source": x["source"], "confidence": x["confidence"]}
                        for r, x in zip(records, rows)],
        "_correct": [p == t for p, t in zip(y_pred, y_true)],
    }


# ------------------------------------------------------------------ output
def save_confusion_png(cm, title, path):
    import matplotlib
    matplotlib.use("Agg")                        # no window, just a file
    import matplotlib.pyplot as plt

    cols = LABELS + ([UNPARSED] if any(cm[t][UNPARSED] for t in LABELS) else [])
    grid = np.array([[cm[t][p] for p in cols] for t in LABELS])
    fig, ax = plt.subplots(figsize=(1.6 + 1.4 * len(cols), 3.2))
    ax.imshow(grid, cmap="Blues")
    ax.set_xticks(range(len(cols)), labels=[c.replace("_", "\n") for c in cols])
    ax.set_yticks(range(len(LABELS)), labels=[c.replace("_", "\n") for c in LABELS])
    ax.set_xlabel("predicted")
    ax.set_ylabel("true")
    ax.set_title(title, fontsize=10)
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            ax.text(j, i, str(grid[i, j]), ha="center", va="center", fontsize=12,
                    color="white" if grid[i, j] > grid.max() / 2 else "black")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return os.path.basename(path)


def to_markdown(s):
    lines = [f"# Evaluation: {s['dataset']} / {s['split']} split (n={s['n']})", "",
             f"Cases by source: {s['by_source_counts']} · by label: {s['by_label_counts']}", "",
             "| Pipeline | Accuracy (95% CI) | Macro-F1 (95% CI) | Bug P / R / F1 | "
             "Failed-TC P / R / F1 | p50 time | Unparsed |",
             "|---|---|---|---|---|---:|---:|"]
    for name, r in s["pipelines"].items():
        m, b, f = r["metrics"], r["metrics"]["bug"], r["metrics"]["failed_testcase"]
        lines.append(
            f"| {name} | {m['accuracy']:.1%} ({r['accuracy_ci'][0]:.1%}–{r['accuracy_ci'][1]:.1%}) | "
            f"{m['macro_f1']:.3f} ({r['macro_f1_ci'][0]:.3f}–{r['macro_f1_ci'][1]:.3f}) | "
            f"{b['precision']:.2f} / {b['recall']:.2f} / {b['f1']:.2f} | "
            f"{f['precision']:.2f} / {f['recall']:.2f} / {f['f1']:.2f} | "
            f"{r['p50_seconds']:.2f} s | {r['unparsed']} |")
    for name, r in s["pipelines"].items():
        cm = r["confusion"]
        lines += ["", f"## {name}", "",
                  "| true \\ predicted | bug | failed_testcase | unparsed |", "|---|---:|---:|---:|"]
        lines += [f"| {t} | {cm[t]['bug']} | {cm[t]['failed_testcase']} | {cm[t][UNPARSED]} |"
                  for t in LABELS]
        lines += ["", "| By framework | n | Accuracy | Macro-F1 |", "|---|---:|---:|---:|"]
        lines += [f"| {g} | {v['n']} | {v['accuracy']:.1%} | {v['macro_f1']:.3f} |"
                  for g, v in r["by_framework"].items()]
        lines += ["", "| By source | n | Accuracy | Macro-F1 |", "|---|---:|---:|---:|"]
        lines += [f"| {g} | {v['n']} | {v['accuracy']:.1%} | {v['macro_f1']:.3f} |"
                  for g, v in r["by_source"].items()]
        if name.startswith("hybrid"):
            lines += ["", f"LLM answered {r['llm_answers_used']} of {s['n']} cases "
                          f"(XGBoost confidence below {s['threshold']})."]
        lines += ["", f"![confusion matrix]({r['confusion_png']})"]
    if s["mcnemar"]:
        lines += ["", "## Paired comparison (exact McNemar)", "",
                  "| A vs B | only A right | only B right | p-value |", "|---|---:|---:|---:|"]
        lines += [f"| {k} | {v['only_a']} | {v['only_b']} | {v['p']:.3f} |"
                  for k, v in s["mcnemar"].items()]
    lines += ["", "Unparsed LLM answers count as wrong. 95% CIs from 1,000 bootstrap "
              "resamples. Groups with small n are indicative only."]
    return "\n".join(lines) + "\n"


# -------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Score classification pipelines.")
    ap.add_argument("--dataset", default="v1")
    ap.add_argument("--split", default="test", choices=["test", "dev", "all"])
    ap.add_argument("--pipeline", nargs="+", default=["xgboost"],
                    choices=ALL_PIPELINES + ["all"])
    ap.add_argument("--threshold", type=float, default=0.7,
                    help="hybrid: ask the LLM when XGBoost confidence is below this")
    ap.add_argument("--limit", type=int, default=0, help="first N cases only")
    args = ap.parse_args()

    records = select(dataset_io.load(args.dataset), args.split, args.limit)
    if not records:
        raise SystemExit("No cases selected - check --dataset and --split.")
    names = ALL_PIPELINES if "all" in args.pipeline else args.pipeline

    out_dir = os.path.join(RESULTS_DIR, f"run_{time.strftime('%Y%m%d-%H%M%S')}_{args.split}")
    os.makedirs(out_dir, exist_ok=True)
    summary = {"dataset": args.dataset, "split": args.split, "n": len(records),
               "limit": args.limit, "threshold": args.threshold,
               "by_source_counts": dict(Counter(r["source"] for r in records)),
               "by_label_counts": dict(Counter(r["label"] for r in records)),
               "pipelines": {}, "mcnemar": {}}

    llm = None
    correct = {}
    for name in names:
        if name in ("llm", "hybrid") and llm is None:
            llm = LLMPredictor()
        predict = {"xgboost": predict_xgboost,
                   "llm": llm,
                   "hybrid": make_hybrid(llm, args.threshold) if llm else None}[name]
        label = name if name == "xgboost" else f"{name} ({llm.name})"
        print(f"\n=== {label} on {len(records)} cases ===")
        result = run_pipeline(name, predict, records)
        correct[label] = result.pop("_correct")
        result["confusion_png"] = save_confusion_png(
            result["confusion"], f"{label} - {args.split} split",
            os.path.join(out_dir, f"confusion_{name}.png"))
        summary["pipelines"][label] = result
        m = result["metrics"]
        print(f"  accuracy {m['accuracy']:.1%}  macro-F1 {m['macro_f1']:.3f}")

    labels = list(correct)
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            p, a, b = mcnemar_p(correct[labels[i]], correct[labels[j]])
            summary["mcnemar"][f"{labels[i]} vs {labels[j]}"] = {"p": p, "only_a": a, "only_b": b}

    with open(os.path.join(out_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    report = to_markdown(summary)
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write(report)
    print("\n" + report)
    print(f"Saved {out_dir}")


if __name__ == "__main__":
    main()