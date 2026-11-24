"""
Generate the outputs to be judged: Jira drafts for bugs, fix suggestions for
failed tests, using the app's own agents.

The branch is chosen by the TRUE label, not by the classifier. That way we
judge generation quality on its own, and a classification mistake doesn't
turn into a "bad Jira draft for a test that wasn't a bug".

Usage (from the project root):
    python -m evaluation.generation.generate --n 30            # 15 bug + 15 failed_testcase
    python -m evaluation.generation.generate --n 4             # quick check

Writes evaluation/results/generation/outputs.jsonl (one line per case).
Cases already in the file are skipped, so you can stop and re-run.
"""
import argparse
import contextlib
import io
import json
import os
import random
import time

from evaluation.datasets import dataset_io

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "results", "generation")
OUT_PATH = os.path.join(OUT_DIR, "outputs.jsonl")


def pick_cases(records, n, seed=42):
    """n cases from the test split, half bug and half failed_testcase,
    spread over frameworks (round-robin), same choice every run."""
    rng = random.Random(seed)
    picked = []
    for label in ("bug", "failed_testcase"):
        by_fw = {}
        for r in sorted(records, key=lambda r: r["id"]):
            if r["split"] == "test" and r["label"] == label:
                by_fw.setdefault(r["framework"], []).append(r)
        for cases in by_fw.values():
            rng.shuffle(cases)
        want, frameworks = n // 2, sorted(by_fw)
        while want and any(by_fw.values()):
            for fw in frameworks:
                if want and by_fw[fw]:
                    picked.append(by_fw[fw].pop())
                    want -= 1
    return picked


def initial_state(record):
    from agents.framework_detector import detect_framework
    inp = dataset_io.to_pipeline_input(record)
    with contextlib.redirect_stdout(io.StringIO()):
        fw = detect_framework(inp["testcase_logs"], inp["testcase_code"],
                              inp["testcase_description"])
    return {**inp, "project_context": "", "framework": fw["framework"],
            "test_type": fw["test_type"], "language": fw["language"],
            "classification": record["label"], "final_output": None}


def render(label, out):
    """The generated output as plain text, the way a reviewer would read it."""
    if label == "bug":
        p = out.get("jira_payload_ready") or out
        steps = "\n".join(f"  {i}. {s}" for i, s in enumerate(p.get("steps_to_reproduce") or [], 1))
        return (f"JIRA DRAFT\nSummary: {p.get('summary', '')}\n"
                f"Severity: {p.get('severity', '')}\n"
                f"Description: {p.get('description', '')}\n"
                f"Steps to reproduce:\n{steps}\n"
                f"Expected: {p.get('expected_result', '')}\n"
                f"Actual: {p.get('actual_result', '')}\n"
                f"Suggested fix: {p.get('suggested_fix', '')}")
    sugg = "\n".join(f"  - {s}" for s in out.get("suggestions") or [])
    changes = "\n".join(f"  - {c}" for c in out.get("changes_made") or [])
    return (f"FIX SUGGESTION\nRoot cause: {out.get('root_cause', '')}\n"
            f"Suggestions:\n{sugg}\nChanges made:\n{changes}\n"
            f"Improved code:\n{out.get('improved_code', '')}")


def claims_text(label, out):
    """Only the statements about what went wrong (checked for hallucinations)."""
    if label == "bug":
        p = out.get("jira_payload_ready") or out
        return " ".join(str(p.get(k, "")) for k in ("summary", "description", "actual_result"))
    return str(out.get("root_cause", ""))


def reference(record):
    """What we know for sure about the case, for the judge's correctness score."""
    who = ("the APPLICATION is wrong (a real bug)" if record["label"] == "bug"
           else "the TEST is wrong (test code, test data or test environment)")
    if record["source"] == "synthetic":
        fault = record["source_ref"].split(":", 1)[-1].replace("_", " ")
        return f"{who}; injected fault: {fault}"
    return f"{who}; real case, no further detail known"


def generate_one(record):
    state = initial_state(record)
    with contextlib.redirect_stdout(io.StringIO()):          # agents print a lot
        if record["label"] == "bug":
            from agents.bug_handler import bug_handler_node
            from agents.jira_generator import jira_generator_node
            state = jira_generator_node(bug_handler_node(state))
        else:
            from agents.failed_testcase import failed_testcase_node
            from agents.code_suggestions import code_suggestions_node
            state = code_suggestions_node(failed_testcase_node(state))
    return state["final_output"] or {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="v1")
    ap.add_argument("--n", type=int, default=30)
    args = ap.parse_args()

    from agents.llm import get_model_info
    info = get_model_info()
    model = f"{info['provider']}:{info['model']}"

    os.makedirs(OUT_DIR, exist_ok=True)
    done = set()
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH, encoding="utf-8") as f:
            done = {json.loads(line)["id"] for line in f if line.strip()}

    cases = pick_cases(dataset_io.load(args.dataset), args.n)
    print(f"{len(cases)} cases ({sum(c['label'] == 'bug' for c in cases)} bug), "
          f"{len(done)} already generated. Generator: {model}")
    for i, r in enumerate(cases, 1):
        if r["id"] in done:
            continue
        start = time.perf_counter()
        try:
            out = generate_one(r)
        except Exception as e:                   # skip, re-run later
            print(f"  [{i}/{len(cases)}] {r['id']}  ERROR {type(e).__name__}: {str(e)[:120]}")
            continue
        inp = dataset_io.to_pipeline_input(r)
        row = {"id": r["id"], "label": r["label"], "framework": r["framework"],
               "source": r["source"], "generator": model,
               "reference": reference(r),
               "input_text": f"DESCRIPTION: {inp['testcase_description']}\n"
                             f"LOGS:\n{inp['testcase_logs']}\nCODE:\n{inp['testcase_code']}",
               "output_text": render(r["label"], out),
               "claims_text": claims_text(r["label"], out),
               "seconds": round(time.perf_counter() - start, 1)}
        with open(OUT_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"  [{i}/{len(cases)}] {r['id']}  {r['label']}  {row['seconds']}s")
    print(f"Saved {OUT_PATH}")


if __name__ == "__main__":
    main()