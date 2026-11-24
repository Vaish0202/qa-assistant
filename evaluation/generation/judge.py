"""
LLM-as-judge for the generated Jira drafts and fix suggestions.

For each output in outputs.jsonl, a judge LLM scores 1-5 on:
    correctness     does it identify the right problem? (checked against the
                    known reference: label + injected fault for synthetic cases)
    groundedness    is every specific claim backed by the log/code?
    actionability   could an engineer act on it without more digging?
and lists unsupported_claims (statements not backed by the input).

A rule-based check (grounding.py) also flags specific facts - exception
names, status codes, quoted names, file paths - that appear in the output's
claims but nowhere in the input.

Judge model: set JUDGE_PROVIDER (ollama | groq) and JUDGE_MODEL in .env.
Use a different, preferably larger, model than the generator; a model
grading its own output tends to be too kind.

Usage (from the project root):
    python -m evaluation.generation.judge
    python -m evaluation.generation.judge --limit 3        # quick check

Writes evaluation/results/generation/judgments.jsonl and judge_report.md.
"""
import argparse
import json
import os
import re
import time

from dotenv import load_dotenv

from evaluation.generation.generate import OUT_DIR, OUT_PATH
from evaluation.generation.grounding import unsupported_facts

load_dotenv()
JUDGMENTS_PATH = os.path.join(OUT_DIR, "judgments.jsonl")
REPORT_PATH = os.path.join(OUT_DIR, "judge_report.md")
DIMENSIONS = ["correctness", "groundedness", "actionability"]

JUDGE_PROMPT = JUDGE_PROMPT = """You are a strict senior QA engineer reviewing output written by an AI assistant
about a failing automated test. Score it with this rubric.

correctness (does it identify the right problem?)
  5 = names the actual cause, consistent with the REFERENCE
  3 = partly right, or right category but vague or partly wrong cause
  1 = wrong cause, or blames the test when the app is wrong (or the reverse)

groundedness (are the output's FACTUAL claims about the failure supported by the input?)
  5 = every factual claim about what happened (error names, values, status codes,
      element names, URLs, where/when it fails) appears in or follows directly from the input
  3 = one invented fact stated as true
  1 = several invented facts stated as true
  Do NOT count: proposed fixes, improved code, best-practice advice, ratings such as
  severity, reproduction steps that follow from the test code, or clearly hedged
  hypotheses ("likely", "possibly", "may"). Those are not claims about what happened.

actionability (could an engineer act on it right away?)
  5 = concrete next step: exact change, file/locator/endpoint, or clear repro steps
  3 = a direction to look in, but generic or mostly guesses
  1 = generic advice that fits any failure ("check the logs", "add error handling")

Also list unsupported_claims: each factual statement in the OUTPUT about what happened
or why it failed, stated as true, that is NOT supported by the input. Apply the same
"Do NOT count" rule. Use an empty list if there are none.

Return ONLY this JSON, nothing else:
{"correctness": <1-5>, "correctness_reason": "<one sentence>",
 "groundedness": <1-5>, "groundedness_reason": "<one sentence>",
 "actionability": <1-5>, "actionability_reason": "<one sentence>",
 "unsupported_claims": ["<claim>", ...]}"""


def get_judge():
    provider = os.getenv("JUDGE_PROVIDER", "ollama").lower()
    if provider == "groq":
        from langchain_groq import ChatGroq
        model = os.getenv("JUDGE_MODEL")
        if not model:
            raise SystemExit("Set JUDGE_MODEL in .env (run scripts/list_groq_models.py).")
        return f"groq:{model}", ChatGroq(model=model, temperature=0,
                                          api_key=os.getenv("GROQ_API_KEY"))
    from langchain_ollama import ChatOllama
    model = os.getenv("JUDGE_MODEL") or os.getenv("OLLAMA_MODEL", "llama3.2")
    return f"ollama:{model}", ChatOllama(model=model, temperature=0,
                                         base_url=os.getenv("OLLAMA_BASE_URL",
                                                            "http://localhost:11434"))


def parse_judgment(text):
    """Pull the JSON out of the judge's answer and check the scores. None if unusable."""
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL)   # Qwen3 reasoning
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        return None
    out = {}
    for dim in DIMENSIONS:
        try:
            score = int(round(float(data.get(dim))))
        except (TypeError, ValueError):
            return None
        if not 1 <= score <= 5:
            return None
        out[dim] = score
        out[f"{dim}_reason"] = str(data.get(f"{dim}_reason", ""))
    claims = data.get("unsupported_claims") or []
    out["unsupported_claims"] = [str(c) for c in claims] if isinstance(claims, list) else [str(claims)]
    return out

def judge_one(llm, row):
    from langchain_core.messages import HumanMessage, SystemMessage
    kind = "Jira bug draft" if row["label"] == "bug" else "fix suggestion for a failing test"
    human = (f"REFERENCE (known truth about this failure): {row['reference']}\n\n"
             f"INPUT the assistant saw:\n{row['input_text']}\n\n"
             f"OUTPUT to review ({kind}):\n{row['output_text']}")
    messages = [SystemMessage(content=JUDGE_PROMPT), HumanMessage(content=human)]
    for attempt in range(2):                     # one retry if the JSON is unusable
        answer = llm.invoke(messages, config={"tags": ["judge"],
                                              "metadata": {"case_id": row["id"]}}).content
        parsed = parse_judgment(answer)
        if parsed:
            return parsed, None
        messages.append(HumanMessage(content="Return ONLY the JSON object described above."))
    return None, f"unparseable judge answer: {answer[:150]!r}"


def load_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def report(judgments, judge_name):
    lines = [f"# Generation quality (judge: {judge_name})", ""]
    groups = [("Jira drafts (bug)", "bug"), ("Fix suggestions (failed_testcase)", "failed_testcase")]
    lines += ["| Output | n | Correctness | Groundedness | Actionability | "
              "Judge: ≥1 unsupported claim | Rule check: ≥1 unsupported fact |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for title, label in groups + [("All", None)]:
        rows = [j for j in judgments if label is None or j["label"] == label]
        if not rows:
            continue
        mean = {d: sum(j[d] for j in rows) / len(rows) for d in DIMENSIONS}
        judge_flag = sum(1 for j in rows if j["unsupported_claims"]) / len(rows)
        rule_flag = sum(1 for j in rows if j["rule_unsupported"]) / len(rows)
        lines.append(f"| {title} | {len(rows)} | {mean['correctness']:.2f} | "
                     f"{mean['groundedness']:.2f} | {mean['actionability']:.2f} | "
                     f"{judge_flag:.0%} | {rule_flag:.0%} |")
    worst = sorted(judgments, key=lambda j: sum(j[d] for d in DIMENSIONS))[:5]
    lines += ["", "## Lowest-scored outputs", "",
              "| Case | C | G | A | Why (correctness) | Unsupported facts (rule check) |",
              "|---|---:|---:|---:|---|---|"]
    for j in worst:
        lines.append(f"| {j['id']} | {j['correctness']} | {j['groundedness']} | "
                     f"{j['actionability']} | {j['correctness_reason'][:90]} | "
                     f"{', '.join(j['rule_unsupported'][:4])} |")
    lines += ["", "Scores are 1-5 means. Judge scores are not yet validated against human "
              "labels (see Cohen's kappa, Step 5)."]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    outputs = load_jsonl(OUT_PATH)
    outputs = list({o["id"]: o for o in outputs}.values())   # one row per case
    if not outputs:
        raise SystemExit("No outputs yet. Run: python -m evaluation.generation.generate")
    if args.limit:
        outputs = outputs[:args.limit]

    judge_name, llm = get_judge()
    generators = {o["generator"] for o in outputs}
    if judge_name in generators:
        print(f"WARNING: the judge ({judge_name}) is also the generator. "
              f"Scores may be too kind; prefer a different, larger judge model.")

    done = {(j["id"], j["judge"]) for j in load_jsonl(JUDGMENTS_PATH)}
    for i, row in enumerate(outputs, 1):
        if (row["id"], judge_name) in done:
            continue
        start = time.perf_counter()
        try:
            scores, error = judge_one(llm, row)
        except Exception as e:
            scores, error = None, f"{type(e).__name__}: {str(e)[:150]}"
        if error:
            print(f"  [{i}/{len(outputs)}] {row['id']}  ERROR {error}")
            continue                              # not saved: retried next run
        record = {"id": row["id"], "label": row["label"], "framework": row["framework"],
                  "judge": judge_name, **scores,
                  "rule_unsupported": unsupported_facts(row["claims_text"], row["input_text"])}
        with open(JUDGMENTS_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"  [{i}/{len(outputs)}] {row['id']}  C={scores['correctness']} "
              f"G={scores['groundedness']} A={scores['actionability']} "
              f"({time.perf_counter() - start:.1f}s)")

    judgments = list({j["id"]: j for j in load_jsonl(JUDGMENTS_PATH) if j["judge"] == judge_name}.values())   # one per case
    md = report(judgments, judge_name)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(md)
    print("\n" + md + f"\nSaved {REPORT_PATH}")


if __name__ == "__main__":
    main()