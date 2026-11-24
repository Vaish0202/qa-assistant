"""
Evaluation CLI: score classification pipelines on a dataset split.

Pipelines
    xgboost   the XGBoost model (52 hand-made features), ~ms per case
    llm       the LLM alone, with the classifier agent's prompt
    hybrid    XGBoost first; if its confidence is below --threshold,
              ask the LLM instead (confidence-gated fallback)

Which cases
    --split test        the frozen test split (default; report this)
    --split dev         for experimenting / choosing settings
    --real-holdout      ALL real GitHub cases, whatever their split.
                        Nothing is trained on them, so they are a clean
                        "trained on synthetic, tested on real" check.

Usage (from the project root):
    python -m evaluation.run --dataset v1 --pipeline xgboost
    python -m evaluation.run --dataset v1 --pipeline xgboost llm hybrid
    python -m evaluation.run --dataset v1 --pipeline all --real-holdout
    python -m evaluation.run --dataset v1 --pipeline llm --limit 5      # quick check

Outputs evaluation/results/run_<date>_<split>/: results.json, report.md,
confusion_<pipeline>.png. LLM answers are cached in evaluation/results/cache/
so re-runs (and the hybrid pipeline) don't call the LLM twice for a case.
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
import time
from collections import Counter, defaultdict

import numpy as np

from evaluation.datasets import dataset_io

LABELS = ["bug", "failed_testcase"]
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
CACHE_DIR = os.path.join(RESULTS_DIR, "cache")


# =============================================================== predictors
def predict_xgboost(record):
    from ml_classifier.predict import predict_classification
    inp = dataset_io.to_pipeline_input(record)
    start = time.perf_counter()
    with contextlib.redirect_stdout(io.StringIO()):          # it prints a line
        out = predict_classification(inp["testcase_logs"], inp["testcase_description"],
                                     inp["testcase_code"])
    return {"pred": out["classification"], "confidence": out["confidence"],
            "seconds": time.perf_counter() - start, "source": "xgboost"}


class LLMPredictor:
    """The classifier agent's LLM prompt, with a disk cache per model."""

    def __init__(self):
        from agents.llm import get_llm, get_model_info
        info = get_model_info()
        self.name = f"{info['provider']}:{info['model']}"
        self.llm = get_llm(info["provider"], info["model"], verbose=False)
        os.makedirs(CACHE_DIR, exist_ok=True)
        safe = self.name.replace(":", "_").replace("/", "_")
        self.cache_path = os.path.join(CACHE_DIR, f"llm_{safe}.jsonl")
        self.cache = {}
        if os.path.exists(self.cache_path):
            with open(self.cache_path, encoding="utf-8") as f:
                for line in f:
                    row = json.loads(line)
                    self.cache[row["key"]] = row

    @staticmethod
    def _key(record):
        inp = dataset_io.to_pipeline_input(record)
        text = json.dumps(inp, sort_keys=True)
        return f"{record['id']}:{hashlib.sha256(text.encode()).hexdigest()[:12]}"

    def __call__(self, record):
        from evaluation.compare_models import (build_messages, invoke_with_retry,
                                               parse_label, text_of)
        key = self._key(record)
        if key in self.cache:
            return {**self.cache[key]["result"], "cached": True}
        start = time.perf_counter()
        try:
            resp = invoke_with_retry(self.llm, build_messages(record),
                                     ["evaluation", f"llm:{self.name}"])
            pred = parse_label(text_of(resp))
            error = None
        except Exception as e:               # count as wrong, keep going
            pred, error = None, f"{type(e).__name__}: {str(e)[:150]}"
        result = {"pred": pred, "confidence": None,
                  "seconds": time.perf_counter() - start, "source": "llm",
                  "error": error}
        if error is None:                   # don't cache failures
            with open(self.cache_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"key": key, "result": result}) + "\n")
            self.cache[key] = {"result": result}
        return result


def llm_name():
    from agents.llm import get_model_info
    info = get_model_info()
    return f"{info['provider']}:{info['model']}"


def make_pipeline(name, threshold, llm_holder):
    def llm():
        if "llm" not in llm_holder:
            llm_holder["llm"] = LLMPredictor()
        return llm_holder["llm"]

    if name == "xgboost":
        return predict_xgboost
    if name == "llm":
        return lambda r: llm()(r)

    def hybrid(record):
        x = predict_xgboost(record)
        if x["confidence"] >= threshold:
            return x
        l = llm()(record)
        return {**l, "seconds": x["seconds"] + l["seconds"], "source": "llm (fallback)"}
    return hybrid


# ================================================================== metrics
def classification_metrics(y_true, y_pred):
    """Accuracy, per-class P/R/F1, macro-F1 over classes present in the sample."""
    n = len(y_true)
    out = {"n": n, "accuracy": sum(t == p for t, p in zip(y_true, y_pred)) / n if n else 0}
    f1s = []
    for label in LABELS:
        tp = sum(t == label and p == label for t, p in zip(y_true, y_pred))
        fp = sum(t != label and p == label for t, p in zip(y_true, y_pred))
        fn = sum(t == label and p != label for t, p in zip(y_true, y_pred))
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        out[label] = {"precision": prec, "recall": rec, "f1": f1, "support": tp + fn}
        if tp + fp + fn:                     # class absent from sample: skip
            f1s.append(f1)
    out["macro_f1"] = float(np.mean(f1s)) if f1s else 0.0
    return out


def bootstrap_ci(y_true, y_pred, metric, n_boot=1000, seed=42):
    """95% CI by resampling cases with replacement."""
    rng = np.random.default_rng(seed)
    y_true, y_pred = np.array(y_true, dtype=object), np.array(y_pred, dtype=object)
    n = len(y_true)
    scores = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        scores.append(classification_metrics(list(y_true[idx]), list(y_pred[idx]))[metric])
    lo, hi = np.percentile(scores, [2.5, 97.5])
    return float(lo), float(hi)


def confusion(y_true, y_pred):
    """rows = true label, columns = predicted (incl. 'unparsed')."""
    cols = LABELS + ["unparsed"]
    return {t: {p: sum(1 for a, b in zip(y_true, y_pred) if a == t and b == p) for p in cols}
            for t in LABELS}


def mcnemar_p(correct_a, correct_b):
    """Exact McNemar test on paired right/wrong outcomes."""
    from scipy.stats import binomtest
    b = sum(1 for x, y in zip(correct_a, correct_b) if x and not y)
    c = sum(1 for x, y in zip(correct_a, correct_b) if y and not x)
    if b + c == 0:
        return 1.0, b, c
    return float(binomtest(min(b, c), b + c, 0.5).pvalue), b, c


def group_metrics(records, preds, key):
    groups = defaultdict(lambda: ([], []))
    for r, p in zip(records, preds):
        groups[r[key]][0].append(r["label"])
        groups[r[key]][1].append(p)
    return {g: {"n": len(t), "accuracy": classification_metrics(t, p)["accuracy"],
                "macro_f1": classification_metrics(t, p)["macro_f1"]}
            for g, (t, p) in sorted(groups.items())}


# ================================================================== outputs
def save_confusion_png(cm, title, path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  (pip install matplotlib to save confusion-matrix images)")
        return None
    cols = LABELS + (["unparsed"] if any(cm[t]["unparsed"] for t in LABELS) else [])
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
            ax.text(j, i, str(grid[i, j]), ha="center", va="center",
                    color="white" if grid[i, j] > grid.max() / 2 else "black", fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return os.path.basename(path)


def to_markdown(summary):
    s = summary
    lines = [f"# Evaluation: {s['dataset']} / {s['selection']} (n={s['n']})", "",
             f"Cases by source: {s['by_source_counts']}  ·  by label: {s['by_label_counts']}", "",
             "| Pipeline | Accuracy (95% CI) | Macro-F1 (95% CI) | Bug P / R | "
             "Failed-TC P / R | p50 time | LLM calls |",
             "|---|---|---|---|---|---:|---:|"]
    for name, r in s["pipelines"].items():
        m = r["metrics"]
        lines.append(
            f"| {name} | {m['accuracy']:.1%} ({r['accuracy_ci'][0]:.1%}–{r['accuracy_ci'][1]:.1%}) | "
            f"{m['macro_f1']:.3f} ({r['macro_f1_ci'][0]:.3f}–{r['macro_f1_ci'][1]:.3f}) | "
            f"{m['bug']['precision']:.2f} / {m['bug']['recall']:.2f} | "
            f"{m['failed_testcase']['precision']:.2f} / {m['failed_testcase']['recall']:.2f} | "
            f"{r['p50_seconds']:.2f} s | {r['llm_calls']} |")
    for name, r in s["pipelines"].items():
        lines += ["", f"## {name}", "", "| By framework | n | Accuracy | Macro-F1 |", "|---|---:|---:|---:|"]
        lines += [f"| {g} | {v['n']} | {v['accuracy']:.1%} | {v['macro_f1']:.3f} |"
                  for g, v in r["by_framework"].items()]
        lines += ["", "| By source | n | Accuracy | Macro-F1 |", "|---|---:|---:|---:|"]
        lines += [f"| {g} | {v['n']} | {v['accuracy']:.1%} | {v['macro_f1']:.3f} |"
                  for g, v in r["by_source"].items()]
        if r.get("confusion_png"):
            lines += ["", f"![confusion matrix]({r['confusion_png']})"]
    if s.get("mcnemar"):
        lines += ["", "## Paired comparison (McNemar, exact)", "",
                  "| A vs B | only A right | only B right | p-value |", "|---|---:|---:|---:|"]
        lines += [f"| {k} | {v['only_a']} | {v['only_b']} | {v['p']:.3f} |"
                  for k, v in s["mcnemar"].items()]
    lines += ["", "Notes: unreadable LLM answers count as wrong. Macro-F1 averages only the "
              "classes present in the sample. 95% CIs from 1,000 bootstrap resamples. "
              "Groups with small n are indicative only."]
    return "\n".join(lines) + "\n"


# ===================================================================== main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--dataset", default="v1")
    ap.add_argument("--split", default="test", choices=["test", "dev", "all"])
    ap.add_argument("--real-holdout", action="store_true",
                    help="evaluate on all real GitHub cases (ignores --split)")
    ap.add_argument("--pipeline", nargs="+", default=["xgboost"],
                    choices=["xgboost", "llm", "hybrid", "all"])
    ap.add_argument("--threshold", type=float, default=0.7,
                    help="hybrid: below this XGBoost confidence, ask the LLM")
    ap.add_argument("--limit", type=int, default=0, help="first N cases only (quick check)")
    args = ap.parse_args()

    records = dataset_io.load(args.dataset)
    if args.real_holdout:
        records = [r for r in records if r["source"] == "github"]
        selection = "real-holdout (all GitHub cases)"
    elif args.split != "all":
        records = [r for r in records if r["split"] == args.split]
        selection = f"{args.split} split"
    else:
        selection = "all cases"
    if args.limit:
        records = records[:args.limit]
        selection += f", first {args.limit}"
    if not records:
        raise SystemExit("No cases selected.")

    names = ["xgboost", "llm", "hybrid"] if "all" in args.pipeline else args.pipeline
    y_true = [r["label"] for r in records]
    summary = {"dataset": args.dataset, "selection": selection, "n": len(records),
               "by_source_counts": dict(Counter(r["source"] for r in records)),
               "by_label_counts": dict(Counter(y_true)),
               "threshold": args.threshold, "pipelines": {}}
    stamp = time.strftime("%Y%m%d-%H%M%S")
    tag = "real" if args.real_holdout else args.split
    out_dir = os.path.join(RESULTS_DIR, f"run_{stamp}_{tag}")
    os.makedirs(out_dir, exist_ok=True)

    llm_holder, correct = {}, {}
    for name in names:
        predict = make_pipeline(name, args.threshold, llm_holder)
        label = name if name == "xgboost" else f"{name} ({llm_name()})"
        print(f"\n=== {label} on {len(records)} cases ===")
        rows = []
        for i, r in enumerate(records, 1):
            res = predict(r)
            rows.append(res)
            mark = "ok" if res["pred"] == r["label"] else ("ERR" if res.get("error") else "x")
            if name != "xgboost":
                cached = " (cached)" if res.get("cached") else ""
                print(f"  [{i}/{len(records)}] {r['id'][:45]:45s} {mark:3s} "
                      f"{res['seconds']:5.1f}s {res['source']}{cached}")
        y_pred = [x["pred"] or "unparsed" for x in rows]
        correct[name] = [p == t for p, t in zip(y_pred, y_true)]
        m = classification_metrics(y_true, y_pred)
        cm = confusion(y_true, y_pred)
        png = save_confusion_png(cm, f"{label}\n{selection}",
                                 os.path.join(out_dir, f"confusion_{name}.png"))
        summary["pipelines"][label] = {
            "metrics": m,
            "accuracy_ci": bootstrap_ci(y_true, y_pred, "accuracy"),
            "macro_f1_ci": bootstrap_ci(y_true, y_pred, "macro_f1"),
            "confusion": cm, "confusion_png": png,
            "by_framework": group_metrics(records, y_pred, "framework"),
            "by_source": group_metrics(records, y_pred, "source"),
            "p50_seconds": float(np.median([x["seconds"] for x in rows])),
            "llm_calls": sum(1 for x in rows if x["source"].startswith("llm") and not x.get("cached")),
            "predictions": [{"id": r["id"], "true": r["label"], "pred": x["pred"],
                             "source": x["source"], "confidence": x.get("confidence")}
                            for r, x in zip(records, rows)],
        }
        print(f"  accuracy {m['accuracy']:.1%}  macro-F1 {m['macro_f1']:.3f}")

    labels = list(summary["pipelines"])
    summary["mcnemar"] = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            p, b, c = mcnemar_p(correct[names[i]], correct[names[j]])
            summary["mcnemar"][f"{labels[i]} vs {labels[j]}"] = {"p": p, "only_a": b, "only_b": c}

    with open(os.path.join(out_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    md = to_markdown(summary)
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write(md)
    print("\n" + md)
    print(f"Saved {out_dir}")


if __name__ == "__main__":
    main()