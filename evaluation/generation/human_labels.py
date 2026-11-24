"""
Step 5: check the LLM judge against your own scores (Cohen's kappa).

1. Make a blind scoring sheet (judge scores are NOT shown, so they can't
   influence you):
       python -m evaluation.generation.human_labels --make-sheet
   -> evaluation/results/generation/review_sheet.md   (read the cases here)
   -> evaluation/results/generation/human_labels.csv  (type your scores here)

2. Score every row in the CSV with the same rubric as the judge
   (correctness, groundedness, actionability: 1-5; hallucination: yes/no).

3. Compare:
       python -m evaluation.generation.human_labels --kappa
   -> evaluation/results/generation/kappa_report.md
"""
import argparse
import csv
import math
import os
import warnings

from sklearn.metrics import cohen_kappa_score

from evaluation.generation.generate import OUT_DIR, OUT_PATH
from evaluation.generation.judge import DIMENSIONS, JUDGMENTS_PATH, get_judge, load_jsonl

SHEET_MD = os.path.join(OUT_DIR, "review_sheet.md")
LABELS_CSV = os.path.join(OUT_DIR, "human_labels.csv")
KAPPA_MD = os.path.join(OUT_DIR, "kappa_report.md")
CSV_FIELDS = ["id", "correctness", "groundedness", "actionability", "hallucination", "notes"]

RUBRIC = """**Rubric** (same as the judge)
- **correctness** 5 = right cause (matches the reference) · 3 = partly right / vague · 1 = wrong cause or wrong side (app vs test)
- **groundedness** 5 = every factual claim about what happened is in the input · 3 = one invented fact stated as true · 1 = several.
  Don't count fixes, improved code, advice, severity, repro steps from the test code, or hedged guesses ("likely").
- **actionability** 5 = concrete next step (exact change / locator / endpoint / repro) · 3 = a direction, but generic · 1 = generic advice
- **hallucination** yes = at least one invented fact stated as true (same rule as groundedness), else no
"""


def make_sheet():
    outputs = list({o["id"]: o for o in load_jsonl(OUT_PATH)}.values())
    if not outputs:
        raise SystemExit("No outputs. Run evaluation.generation.generate first.")
    if os.path.exists(LABELS_CSV):
        raise SystemExit(f"{LABELS_CSV} already exists - not overwriting your scores.")
    parts = ["# Blind review sheet", "", RUBRIC]
    for i, o in enumerate(outputs, 1):
        parts += ["---", f"## {i}. `{o['id']}`  ({o['label']})", "",
                  f"**Reference:** {o['reference']}", "",
                  "**Input the assistant saw**", "```", o["input_text"].strip(), "```", "",
                  "**Output to score**", "```", o["output_text"].strip(), "```", ""]
    with open(SHEET_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    with open(LABELS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for o in outputs:
            w.writerow({"id": o["id"]})
    print(f"Read the cases in:  {SHEET_MD}\nType your scores in: {LABELS_CSV}")


def agreement(human, judge):
    """Exact agreement, within-1 agreement, Cohen's kappa and quadratic-weighted kappa.
    Kappa is None when it is undefined (e.g. both raters gave one single value)."""
    n = len(human)
    exact = sum(h == j for h, j in zip(human, judge)) / n
    ordinal = not isinstance(human[0], bool)       # 1-5 scores, not yes/no
    within1 = sum(abs(h - j) <= 1 for h, j in zip(human, judge)) / n if ordinal else None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")          # sklearn warns when kappa is undefined
        k = cohen_kappa_score(human, judge)
        kw = cohen_kappa_score(human, judge, weights="quadratic") if within1 is not None else None
    clean = lambda v: None if v is None or (isinstance(v, float) and math.isnan(v)) else float(v)
    return {"n": n, "exact": exact, "within1": within1, "kappa": clean(k), "weighted_kappa": clean(kw)}


def read_labels():
    with open(LABELS_CSV, encoding="utf-8-sig") as f:      # Excel may add a BOM
        rows = list(csv.DictReader(f))
    labels, problems = {}, []
    for r in rows:
        try:
            scores = {d: int(r[d]) for d in DIMENSIONS}
            if not all(1 <= v <= 5 for v in scores.values()):
                raise ValueError
            hall = r["hallucination"].strip().lower()
            if hall not in ("yes", "no"):
                raise ValueError
        except (ValueError, TypeError, KeyError):
            problems.append(r.get("id", "?"))
            continue
        labels[r["id"]] = {**scores, "hallucination": hall == "yes"}
    return labels, problems


def kappa():
    labels, problems = read_labels()
    if problems:
        print(f"Skipping {len(problems)} row(s) with missing/invalid scores: {problems[:5]}")
    judge_name, _ = get_judge()
    judgments = {j["id"]: j for j in load_jsonl(JUDGMENTS_PATH) if j["judge"] == judge_name}
    ids = [i for i in labels if i in judgments]
    if len(ids) < 10:
        raise SystemExit(f"Only {len(ids)} cases have both your score and a {judge_name} score.")

    rows = []
    for dim in DIMENSIONS:
        rows.append((dim, agreement([labels[i][dim] for i in ids],
                                    [judgments[i][dim] for i in ids])))
    rows.append(("hallucination (yes/no)",
                 agreement([labels[i]["hallucination"] for i in ids],
                           [bool(judgments[i]["unsupported_claims"]) for i in ids])))

    fmt = lambda v: "undefined" if v is None else f"{v:.2f}"
    pct = lambda v: "-" if v is None else f"{v:.0%}"
    lines = [f"# Judge vs human (judge: {judge_name}, n={len(ids)})", "",
             "| Dimension | Exact agreement | Within ±1 | Cohen's κ | Weighted κ (quadratic) |",
             "|---|---:|---:|---:|---:|"]
    lines += [f"| {d} | {pct(a['exact'])} | {pct(a['within1'])} | {fmt(a['kappa'])} | "
              f"{'-' if a['within1'] is None else fmt(a['weighted_kappa'])} |" for d, a in rows]
    human_mean = {d: sum(labels[i][d] for i in ids) / len(ids) for d in DIMENSIONS}
    judge_mean = {d: sum(judgments[i][d] for i in ids) / len(ids) for d in DIMENSIONS}
    lines += ["", "| Mean score | Human | Judge |", "|---|---:|---:|"]
    lines += [f"| {d} | {human_mean[d]:.2f} | {judge_mean[d]:.2f} |" for d in DIMENSIONS]
    disagree = [i for i in ids if any(abs(labels[i][d] - judgments[i][d]) >= 2 for d in DIMENSIONS)
                or labels[i]["hallucination"] != bool(judgments[i]["unsupported_claims"])]
    lines += ["", f"Cases where you and the judge disagree (≥2 points, or on hallucination): "
                  f"{', '.join(disagree) or 'none'}", "",
              "κ: 1 = perfect, 0 = chance level, >0.6 usually called substantial. "
              "When almost every score is the same value, κ can be low or undefined even "
              "with high exact agreement (the 'kappa paradox'); read it next to exact agreement."]
    md = "\n".join(lines) + "\n"
    with open(KAPPA_MD, "w", encoding="utf-8") as f:
        f.write(md)
    print(md + f"\nSaved {KAPPA_MD}")


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--make-sheet", action="store_true")
    g.add_argument("--kappa", action="store_true")
    args = ap.parse_args()
    make_sheet() if args.make_sheet else kappa()


if __name__ == "__main__":
    main()