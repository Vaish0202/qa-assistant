"""
Compare LLMs on the classification task: accuracy vs p95 latency vs cost.

Each model classifies every case in a dataset split with the SAME prompt the
classifier agent uses (framework-specific few-shot + chain of thought).

Usage (from the project root):
    python -m evaluation.compare_models \
        --models ollama:llama3.2 groq:openai/gpt-oss-20b \
                 bedrock:amazon.nova-micro-v1:0 bedrock:amazon.nova-lite-v1:0 \
        --split test

    --limit 5        quick check on the first 5 cases
    --split dev      use while experimenting; report test only once at the end

Writes evaluation/results/model_comparison.md and .json
"""
import argparse
import contextlib
import io
import json
import os
import re
import time

import numpy as np
from langchain_core.messages import HumanMessage, SystemMessage

from agents.framework_detector import detect_framework
from agents.llm import get_llm
from agents.prompts import CLASSIFIER_PROMPTS, get_prompt
from evaluation.datasets import dataset_io
from evaluation.pricing import cost_usd, has_price

LABELS = ["bug", "failed_testcase"]
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


# ------------------------------------------------------------- one prediction
def build_messages(record):
    """Same prompt as the classifier agent (agents/classifier.py)."""
    inp = dataset_io.to_pipeline_input(record)
    with contextlib.redirect_stdout(io.StringIO()):
        framework = detect_framework(inp["testcase_logs"], inp["testcase_code"],
                                     inp["testcase_description"])["framework"]
    return [
        SystemMessage(content=get_prompt(CLASSIFIER_PROMPTS, framework)),
        HumanMessage(content=f"""
FRAMEWORK: {framework}
LOGS: {inp['testcase_logs']}
CODE: {inp['testcase_code']}
"""),
    ]


def parse_label(text: str):
    """Pull {"classification": ...} out of the reply. None if unreadable."""
    match = re.search(r"\{.*\}", text or "", re.DOTALL)
    try:
        label = json.loads(match.group() if match else text).get("classification")
    except (json.JSONDecodeError, AttributeError):
        return None
    return label if label in LABELS else None


def invoke_with_retry(llm, messages, tags, retries=3):
    for attempt in range(retries):
        try:
            return llm.invoke(messages, config={"tags": tags})
        except Exception as e:                      # throttling, timeouts
            if attempt == retries - 1:
                raise
            wait = 2 ** (attempt + 1)
            print(f"    retry in {wait}s ({type(e).__name__}: {str(e)[:80]})")
            time.sleep(wait)


def text_of(response) -> str:
    """Message text; some models return a list of content blocks."""
    content = response.content
    if isinstance(content, list):
        return "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
    return content


# --------------------------------------------------------------- one model
def run_model(spec, records):
    provider, model = spec.split(":", 1)
    llm = get_llm(provider, model, verbose=False)
    tags = ["model-comparison", f"llm:{model}", f"provider:{provider}"]
    rows = []
    for i, r in enumerate(records, 1):
        start = time.perf_counter()
        error = None
        try:
            resp = invoke_with_retry(llm, build_messages(r), tags)
            seconds = time.perf_counter() - start
            pred = parse_label(text_of(resp))
            usage = getattr(resp, "usage_metadata", None) or {}
        except Exception as e:
            seconds, pred, usage, error = time.perf_counter() - start, None, {}, str(e)[:200]
        p, c = usage.get("input_tokens", 0), usage.get("output_tokens", 0)
        rows.append({"id": r["id"], "framework": r["framework"], "source": r["source"],
                     "true": r["label"], "pred": pred, "seconds": seconds,
                     "prompt_tokens": p, "completion_tokens": c,
                     "cost_usd": cost_usd(model, p, c), "error": error})
        mark = "ok" if pred == r["label"] else ("ERR" if error else "x")
        print(f"  [{i}/{len(records)}] {r['id']:40s} {mark:3s} {seconds:5.1f}s")
    return provider, model, rows


def summarize(provider, model, rows):
    n = len(rows)
    y_true = [r["true"] for r in rows]
    # Unreadable answers count as wrong.
    y_pred = [r["pred"] or "unparsed" for r in rows]
    f1s = []
    for label in LABELS:
        tp = sum(t == label and p == label for t, p in zip(y_true, y_pred))
        fp = sum(t != label and p == label for t, p in zip(y_true, y_pred))
        fn = sum(t == label and p != label for t, p in zip(y_true, y_pred))
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if prec + rec else 0.0)
    ok_lat = [r["seconds"] for r in rows if not r["error"]]
    return {
        "provider": provider, "model": model, "n": n,
        "accuracy": sum(t == p for t, p in zip(y_true, y_pred)) / n,
        "macro_f1": float(np.mean(f1s)),
        "unparsed": sum(r["pred"] is None and not r["error"] for r in rows),
        "errors": sum(bool(r["error"]) for r in rows),
        "p50_s": float(np.percentile(ok_lat, 50)) if ok_lat else float("nan"),
        "p95_s": float(np.percentile(ok_lat, 95)) if ok_lat else float("nan"),
        "avg_tokens": float(np.mean([r["prompt_tokens"] + r["completion_tokens"] for r in rows])),
        "cost_per_1k_usd": float(np.mean([r["cost_usd"] for r in rows]) * 1000),
        "price_known": has_price(model),
    }


def to_markdown(summaries, split, dataset):
    lines = [f"## LLM comparison ({dataset} {split} split, n={summaries[0]['n']})", "",
             "| Provider | Model | Accuracy | Macro-F1 | p50 latency | p95 latency | "
             "Avg tokens | Cost / 1k classifications | Errors |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for s in sorted(summaries, key=lambda s: -s["macro_f1"]):
        cost = f"${s['cost_per_1k_usd']:.3f}" if s["price_known"] else "n/a (add price)"
        if s["provider"] == "ollama":
            cost = "$0 (local)"
        lines.append(f"| {s['provider']} | `{s['model']}` | {s['accuracy']:.1%} | "
                     f"{s['macro_f1']:.3f} | {s['p50_s']:.2f} s | {s['p95_s']:.2f} s | "
                     f"{s['avg_tokens']:.0f} | {cost} | {s['errors'] + s['unparsed']} |")
    lines += ["", "Same prompt for every model (the classifier agent's framework-specific "
              "few-shot prompt), temperature 0. Unreadable answers and API errors count "
              "as wrong. Latency is measured from this machine and includes network time. "
              "Prices from evaluation/pricing.py."]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", required=True,
                    help="provider:model, e.g. bedrock:amazon.nova-micro-v1:0")
    ap.add_argument("--dataset", default="v1")
    ap.add_argument("--split", default="test", choices=["dev", "test"])
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    records = dataset_io.load(args.dataset, split=args.split)
    if args.limit:
        records = records[:args.limit]
    if not records:
        raise SystemExit(f"No records in the {args.split} split")

    summaries, all_rows = [], {}
    for spec in args.models:
        print(f"\n=== {spec} ===")
        provider, model, rows = run_model(spec, records)
        summaries.append(summarize(provider, model, rows))
        all_rows[spec] = rows

    os.makedirs(RESULTS_DIR, exist_ok=True)
    md = to_markdown(summaries, args.split, args.dataset)
    with open(os.path.join(RESULTS_DIR, "model_comparison.md"), "w", encoding="utf-8") as f:
        f.write(md)
    with open(os.path.join(RESULTS_DIR, "model_comparison.json"), "w", encoding="utf-8") as f:
        json.dump({"summaries": summaries, "predictions": all_rows}, f, indent=2)
    print("\n" + md)
    print(f"Saved {RESULTS_DIR}/model_comparison.md and .json")


if __name__ == "__main__":
    main()