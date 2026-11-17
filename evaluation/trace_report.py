"""
Observability benchmark: run the sample cases through the full pipeline
with LangSmith tracing on, then pull the traces back and report per agent:
latency p50/p95, prompt/completion tokens, and cost per classification.

Usage (from the project root):
    python evaluation/trace_report.py            # all 30 cases
    python evaluation/trace_report.py --n 5      # quick check
    python evaluation/trace_report.py --batch-id <id>   # re-report an old batch

Writes: evaluation/results/observability_report.md (+ .csv)
"""
import argparse
import csv
import os
import sys
import time
import uuid
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import numpy as np
from langsmith import Client

from evaluation.pricing import cost_usd, reference_cost_usd, REFERENCE_MODEL

AGENT_TAG_PREFIX = "agent:"
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


# ---------------------------------------------------------------- 1. run cases
def run_batch(n: int, batch_id: str) -> int:
    from agents.graph import run_analysis
    from sample_data.test_cases import TEST_CASES

    cases = TEST_CASES[:n] if n else TEST_CASES

    # Load XGBoost once up front so case 1 doesn't include disk loading time.
    try:
        from ml_classifier.predict import get_model
        get_model()
    except FileNotFoundError:
        pass

    for i, tc in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {tc['id']}")
        run_analysis(
            testcase_logs=tc["testcase_logs"],
            testcase_description=tc["testcase_description"],
            testcase_code=tc["testcase_code"],
            user_id="observability_benchmark",
            extra_tags=["benchmark"],
            extra_metadata={"batch_id": batch_id, "case_id": tc["id"],
                            "expected": tc["expected"]},
        )

    # Traces upload in the background; make sure they are all sent.
    try:
        from langsmith.run_trees import get_cached_client
        get_cached_client().flush()
    except Exception:
        pass
    try:
        from langchain_core.tracers.langchain import wait_for_all_tracers
        wait_for_all_tracers()
    except Exception:
        pass
    return len(cases)


# ------------------------------------------------------ 2. fetch from LangSmith
def fetch_runs(client: Client, project: str, batch_id: str, expected_roots):
    batch_filter = (f'and(eq(metadata_key, "batch_id"), '
                    f'eq(metadata_value, "{batch_id}"))')

    # LangSmith needs a few seconds to index new traces.
    roots = []
    for _ in range(12):
        roots = list(client.list_runs(project_name=project, is_root=True,
                                      filter=batch_filter))
        finished = [r for r in roots if r.end_time is not None]
        if expected_roots is None or len(finished) >= expected_roots:
            break
        print(f"  waiting for traces… {len(finished)}/{expected_roots}")
        time.sleep(5)

    all_runs = list(client.list_runs(project_name=project,
                                     trace_filter=batch_filter))
    return roots, all_runs


# ---------------------------------------------------------------- 3. aggregate
def seconds(run) -> float:
    if run.start_time is None or run.end_time is None:
        return float("nan")
    return (run.end_time - run.start_time).total_seconds()


def agent_of(run):
    for tag in run.tags or []:
        if tag.startswith(AGENT_TAG_PREFIX):
            return tag[len(AGENT_TAG_PREFIX):]
    return None


def llm_model(run) -> str:
    meta = (run.extra or {}).get("metadata", {}) or {}
    return meta.get("ls_model_name") or meta.get("llm_model") or "unknown"


def aggregate(roots, all_runs):
    by_id = {r.id: r for r in all_runs}

    def owning_agent(run):
        """Walk up the tree to the nearest '<name>_agent' run."""
        cur = run
        while cur is not None:
            # Child runs inherit the agent tag too, so also check the name.
            if cur.name.endswith("_agent") and agent_of(cur):
                return agent_of(cur)
            cur = by_id.get(cur.parent_run_id)
        return None

    agent_latency = defaultdict(list)
    agent_runs_count = defaultdict(int)
    agent_tokens = defaultdict(lambda: {"prompt": 0, "completion": 0})
    agent_cost = defaultdict(float)
    agent_ref_cost = defaultdict(float)
    trace_cost = defaultdict(float)
    trace_ref_cost = defaultdict(float)
    trace_tokens = defaultdict(int)
    xgb_latency = []

    for run in all_runs:
        if run.name.endswith("_agent") and agent_of(run):          # agent runs
            name = agent_of(run)
            agent_latency[name].append(seconds(run))
            agent_runs_count[name] += 1
        elif run.name == "xgboost_classifier":                    # XGBoost
            xgb_latency.append(seconds(run))
        elif run.run_type == "llm":                               # LLM calls
            name = owning_agent(run) or "unattributed"
            p = run.prompt_tokens or 0
            c = run.completion_tokens or 0
            usd = cost_usd(llm_model(run), p, c)
            ref = reference_cost_usd(p, c)
            agent_tokens[name]["prompt"] += p
            agent_tokens[name]["completion"] += c
            agent_cost[name] += usd
            agent_ref_cost[name] += ref
            trace_cost[run.trace_id] += usd
            trace_ref_cost[run.trace_id] += ref
            trace_tokens[run.trace_id] += p + c

    rows = []
    for name in sorted(agent_latency):
        lat = np.array([x for x in agent_latency[name] if not np.isnan(x)])
        n = agent_runs_count[name]
        tok = agent_tokens[name]
        rows.append({
            "agent": name,
            "runs": n,
            "p50_s": float(np.percentile(lat, 50)) if len(lat) else float("nan"),
            "p95_s": float(np.percentile(lat, 95)) if len(lat) else float("nan"),
            "avg_prompt_tokens": tok["prompt"] / n if n else 0,
            "avg_completion_tokens": tok["completion"] / n if n else 0,
            "avg_cost_usd": agent_cost[name] / n if n else 0,
            "avg_ref_cost_usd": agent_ref_cost[name] / n if n else 0,
        })

    root_lat = np.array([seconds(r) for r in roots if r.end_time is not None])
    costs = [trace_cost.get(r.trace_id, 0.0) for r in roots]
    ref_costs = [trace_ref_cost.get(r.trace_id, 0.0) for r in roots]
    tokens = [trace_tokens.get(r.trace_id, 0) for r in roots]
    summary = {
        "traces": len(roots),
        "e2e_p50_s": float(np.percentile(root_lat, 50)) if len(root_lat) else float("nan"),
        "e2e_p95_s": float(np.percentile(root_lat, 95)) if len(root_lat) else float("nan"),
        "avg_tokens_per_classification": float(np.mean(tokens)) if tokens else 0,
        "avg_cost_per_classification_usd": float(np.mean(costs)) if costs else 0,
        "avg_ref_cost_per_classification_usd": float(np.mean(ref_costs)) if ref_costs else 0,
        "xgb_p50_ms": float(np.percentile(xgb_latency, 50) * 1000) if xgb_latency else float("nan"),
        "xgb_p95_ms": float(np.percentile(xgb_latency, 95) * 1000) if xgb_latency else float("nan"),
        "models": sorted({llm_model(r) for r in all_runs if r.run_type == "llm"}),
    }
    return rows, summary


# ------------------------------------------------------------------- 4. output
def to_markdown(rows, summary, batch_id) -> str:
    lines = [
        f"## Observability report (batch `{batch_id}`)",
        "",
        f"Traces: {summary['traces']} · LLM: {', '.join(summary['models']) or 'none'}",
        "",
        "| Agent | Runs | p50 latency | p95 latency | Avg prompt tokens | "
        f"Avg completion tokens | Actual cost / run | Est. cost on {REFERENCE_MODEL} / run |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['agent']} | {r['runs']} | {r['p50_s']:.2f} s | {r['p95_s']:.2f} s | "
            f"{r['avg_prompt_tokens']:.0f} | {r['avg_completion_tokens']:.0f} | "
            f"${r['avg_cost_usd']:.6f} | ${r['avg_ref_cost_usd']:.6f} |"
        )
    ref = summary['avg_ref_cost_per_classification_usd']
    lines += [
        "",
        f"- End-to-end latency: p50 {summary['e2e_p50_s']:.2f} s, "
        f"p95 {summary['e2e_p95_s']:.2f} s",
        f"- XGBoost classifier: p50 {summary['xgb_p50_ms']:.1f} ms, "
        f"p95 {summary['xgb_p95_ms']:.1f} ms",
        f"- Tokens per classification: {summary['avg_tokens_per_classification']:.0f}",
        f"- Cost per classification: ${summary['avg_cost_per_classification_usd']:.6f} actual, "
        f"${ref:.6f} estimated on {REFERENCE_MODEL} (≈ ${ref * 1000:.2f} per 1,000)",
        "",
        "Latency is wall-clock time per agent run, including the LLM call. "
        "Bug-path agents (bug_handler, jira_generator) and failed-test-path agents "
        "(failed_testcase_handler, code_suggestions) only run for their own cases, "
        "so their run counts are lower than the classifier's.",
    ]
    return "\n".join(lines) + "\n"


def save(rows, summary, batch_id):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    md_path = os.path.join(RESULTS_DIR, "observability_report.md")
    csv_path = os.path.join(RESULTS_DIR, "observability_report.csv")
    md = to_markdown(rows, summary, batch_id)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        if rows:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    print("\n" + md)
    print(f"Saved {md_path}\nSaved {csv_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=0, help="number of cases (0 = all)")
    ap.add_argument("--batch-id", help="report an existing batch instead of running")
    args = ap.parse_args()

    if os.getenv("LANGSMITH_TRACING", "").lower() != "true" or not os.getenv("LANGSMITH_API_KEY"):
        sys.exit("Set LANGSMITH_TRACING=true and LANGSMITH_API_KEY in .env first.")
    project = os.getenv("LANGSMITH_PROJECT", "default")

    if args.batch_id:
        batch_id, expected = args.batch_id, None
    else:
        batch_id = f"bench-{uuid.uuid4().hex[:8]}"
        print(f"Batch id: {batch_id}  (LangSmith project: {project})")
        expected = run_batch(args.n, batch_id)

    roots, all_runs = fetch_runs(Client(), project, batch_id, expected)
    if not roots:
        sys.exit("No traces found. Check LANGSMITH_PROJECT and your API key.")
    rows, summary = aggregate(roots, all_runs)
    save(rows, summary, batch_id)


if __name__ == "__main__":
    main()