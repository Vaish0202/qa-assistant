"""
Mine real test failures from public GitHub issues, and pre-label them by
how they were fixed.

How it works:
  1. Search closed GitHub issues that contain a failing-test log
     (pytest "FAILED tests/...", Selenium/Playwright/SQLAlchemy/requests errors).
  2. Find what closed the issue: a merged pull request or a commit.
  3. Look at the files that fix changed:
        only test files changed            -> proposed label "failed_testcase"
        application (non-test) code changed -> proposed label "bug"
        neither (docs, CI config only)     -> skipped
  4. Pull the failing test function from the repo, at the version before the fix.
  5. Write everything to github_candidates.csv for YOU to review.

Nothing goes into v1.jsonl until you review it and run --merge.

Needs a GitHub token (no special permissions, public repos only):
  github.com -> Settings -> Developer settings -> Personal access tokens
  -> Fine-grained -> "Public repositories (read-only)". Put it in .env:
        GITHUB_TOKEN=github_pat_...

Usage (from the project root):
    python -m evaluation.datasets.mine_github --limit 40          # search + pre-label
    # open evaluation/datasets/github_candidates.csv, fill keep / final_label
    python -m evaluation.datasets.mine_github --merge              # add reviewed cases to v1
"""
import argparse
import ast
import base64
import contextlib
import csv
import io as _io
import os
import re
import sys
import time

import requests
from dotenv import load_dotenv

from evaluation.datasets import dataset_io
from evaluation.datasets.schema import DETECTOR_TO_DATASET, LABELS

load_dotenv()

API = "https://api.github.com"
CANDIDATES_CSV = os.path.join(dataset_io.DATASETS_DIR, "github_candidates.csv")

# One query per framework, so each framework gets a fair share of results.
QUERIES = {
    "selenium": '"selenium.common.exceptions" "FAILED" in:body is:issue is:closed language:Python',
    "playwright": '"playwright._impl._errors" "FAILED" in:body is:issue is:closed language:Python',
    "api": '"requests.exceptions" "FAILED tests" in:body is:issue is:closed language:Python',
    "db": '"sqlalchemy.exc" "FAILED tests" in:body is:issue is:closed language:Python',
    "unit": '"FAILED tests/" "AssertionError" in:body is:issue is:closed language:Python',
}

CSV_FIELDS = ["id", "keep", "final_label", "proposed_label", "label_reason",
              "framework", "issue_url", "fix_url", "files_changed",
              "test_ref", "log_excerpt"]

# ------------------------------------------------------------------ helpers
TEST_PATH = re.compile(r"(^|/)(tests?|testing)/|(^|/)test_[^/]*\.py$|_test\.py$|"
                       r"(^|/)conftest\.py$|\.(spec|test)\.[jt]sx?$")
NON_CODE = re.compile(r"\.(md|rst|txt|ya?ml|toml|cfg|ini|json|lock)$|^\.github/|^docs?/",
                      re.IGNORECASE)


def is_test_file(path: str) -> bool:
    return bool(TEST_PATH.search(path))


def propose_label(files: list):
    """Decide the label from the files the fix changed.

    Returns (label or None, reason). None means "can't tell, skip it".
    """
    code = [f for f in files if not NON_CODE.search(f)]
    tests = [f for f in code if is_test_file(f)]
    app = [f for f in code if not is_test_file(f)]
    if app:
        return "bug", f"fix changed app code: {', '.join(app[:3])}"
    if tests:
        return "failed_testcase", f"fix changed only tests: {', '.join(tests[:3])}"
    return None, "fix changed no code (docs/CI only)"


FENCE = re.compile(r"```[a-zA-Z]*\n(.*?)```", re.DOTALL)
ERROR_HINT = re.compile(r"Traceback|FAILED|Error|Exception|assert ", re.IGNORECASE)


def extract_log(body: str) -> str:
    """The code block in the issue that looks most like a test failure."""
    blocks = [b.strip() for b in FENCE.findall(body or "")]
    blocks = [b for b in blocks if ERROR_HINT.search(b)]
    if not blocks:
        return ""
    best = max(blocks, key=lambda b: len(ERROR_HINT.findall(b)))
    return best[-4000:]          # keep the end, where the error is


NODE_ID = re.compile(r"((?:[\w.-]+/)*test_[\w]+\.py)::(?:\w+::)?(test_\w+)")
TB_FRAME = re.compile(r'File "([^"]*test[^"]*\.py)", line \d+, in (test_\w+)')


def find_test_ref(log: str):
    """(test file path, test function name) from a pytest node id or traceback."""
    m = NODE_ID.search(log) or TB_FRAME.search(log)
    if not m:
        return None, None
    path = m.group(1)
    # Absolute paths in tracebacks: keep the part from "tests/" on.
    idx = path.find("tests/") if "tests/" in path else path.find("test/")
    return (path[idx:] if idx > 0 else path.lstrip("/")), m.group(2)


def extract_function(source: str, name: str) -> str:
    """Source code of def <name> (also inside a class), or ''."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    return ""


STACK_LINE = re.compile(r'^\s*(Traceback \(most|File ".*", line \d+|\S+\.py:\d+: in )')


def split_log(text: str):
    log, stack = [], []
    for ln in text.splitlines():
        (stack if STACK_LINE.match(ln) else log).append(ln)
    return "\n".join(log).strip(), "\n".join(stack).strip()


def framework_for(log, code, query_framework):
    from agents.framework_detector import detect_framework
    with contextlib.redirect_stdout(_io.StringIO()):
        detected = detect_framework(log, code, "")["framework"]
    mapped = DETECTOR_TO_DATASET.get(detected)
    # A specific detection (selenium, api, db, ...) wins; otherwise use the
    # framework the search query was for. Check it during review anyway.
    if mapped and mapped != "unit":
        return mapped
    return query_framework

# ------------------------------------------------------------- GitHub client
class GitHub:
    def __init__(self, token):
        self.s = requests.Session()
        self.s.headers.update({"Authorization": f"Bearer {token}",
                               "Accept": "application/vnd.github+json",
                               "X-GitHub-Api-Version": "2022-11-28"})

    def get(self, url, **params):
        for attempt in range(3):
            r = self.s.get(url if url.startswith("http") else API + url,
                           params=params, timeout=30)
            if r.status_code == 403 and r.headers.get("X-RateLimit-Remaining") == "0":
                wait = max(5, int(r.headers.get("X-RateLimit-Reset", time.time() + 60)) - int(time.time()))
                print(f"  rate limited, waiting {wait}s")
                time.sleep(min(wait, 120))
                continue
            if r.status_code in (404, 410, 422):
                return None
            r.raise_for_status()
            return r.json()
        return None

    def search_issues(self, query, per_page=30, page=1):
        time.sleep(2.1)                     # search API: 30 requests/minute
        data = self.get("/search/issues", q=query, per_page=per_page, page=page)
        return (data or {}).get("items", [])

    def fix_for_issue(self, owner, repo, number):
        """Return (kind, url, files, base_sha) for what closed the issue."""
        events = self.get(f"/repos/{owner}/{repo}/issues/{number}/timeline", per_page=100) or []
        for ev in events:                   # 1. a merged PR that references the issue
            src = (ev.get("source") or {}).get("issue") or {}
            pr = src.get("pull_request") or {}
            if ev.get("event") == "cross-referenced" and pr.get("merged_at"):
                pr_repo = src["repository_url"].split("/repos/")[1]
                if pr_repo.lower() != f"{owner}/{repo}".lower():
                    continue
                files = self.get(f"/repos/{pr_repo}/pulls/{src['number']}/files", per_page=100) or []
                pull = self.get(f"/repos/{pr_repo}/pulls/{src['number']}") or {}
                return ("pr", src["html_url"], [f["filename"] for f in files],
                        (pull.get("base") or {}).get("sha"))
        for ev in events:                   # 2. closed directly by a commit
            if ev.get("event") == "closed" and ev.get("commit_id"):
                commit = self.get(f"/repos/{owner}/{repo}/commits/{ev['commit_id']}") or {}
                parents = commit.get("parents") or [{}]
                return ("commit", commit.get("html_url", ""),
                        [f["filename"] for f in commit.get("files", [])],
                        parents[0].get("sha"))
        return None, None, [], None

    def file_at(self, owner, repo, path, ref):
        data = self.get(f"/repos/{owner}/{repo}/contents/{path}", ref=ref) if ref else None
        if not data or data.get("encoding") != "base64":
            return ""
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")

# ----------------------------------------------------------------- mining
def mine(limit_per_framework: int):
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        sys.exit("Set GITHUB_TOKEN in .env (see the top of this file).")
    gh = GitHub(token)
    existing = {r["id"] for r in dataset_io.load("v1")} if os.path.exists(
        dataset_io.dataset_path("v1")) else set()
    rows, seen = [], set()

    for fw, query in QUERIES.items():
        print(f"\n[{fw}] {query}")
        kept, page = 0, 1
        while kept < limit_per_framework and page <= 5:
            items = gh.search_issues(query, page=page)
            if not items:
                break
            page += 1
            for issue in items:
                if kept >= limit_per_framework:
                    break
                owner, repo = issue["repository_url"].split("/repos/")[1].split("/")
                rid = f"gh-{owner}-{repo}-{issue['number']}".lower()
                if rid in seen or rid in existing:
                    continue
                seen.add(rid)

                log = extract_log(issue.get("body", ""))
                if not log:
                    continue
                kind, fix_url, files, base_sha = gh.fix_for_issue(owner, repo, issue["number"])
                if not files:
                    print(f"  skip {rid}: no linked fix")
                    continue
                label, reason = propose_label(files)
                if not label:
                    print(f"  skip {rid}: {reason}")
                    continue

                test_path, test_name = find_test_ref(log)
                code = ""
                if test_path and test_name:
                    code = extract_function(gh.file_at(owner, repo, test_path, base_sha), test_name)

                rows.append({
                    "id": rid, "keep": "", "final_label": "",
                    "proposed_label": label, "label_reason": reason,
                    "framework": framework_for(log, code, fw),
                    "issue_url": issue["html_url"], "fix_url": fix_url,
                    "files_changed": "; ".join(files[:10]),
                    "test_ref": f"{test_path}::{test_name}" if test_name else "",
                    "log_excerpt": log,
                    "_code": code, "_title": issue.get("title", ""),
                })
                kept += 1
                print(f"  + {rid}: {label} ({reason[:60]})")

    # Code and title go to a side file; the CSV stays readable in Excel.
    with open(CANDIDATES_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    dataset_io.save(CANDIDATES_CSV.replace(".csv", ".jsonl"), rows)
    print(f"\nWrote {len(rows)} candidates to {CANDIDATES_CSV}")
    print("Review it: set keep=yes/no and final_label=bug/failed_testcase, then run --merge")


# ------------------------------------------------------------------ merge
def merge():
    with open(CANDIDATES_CSV, encoding="utf-8") as f:
        reviewed = {r["id"]: r for r in csv.DictReader(f)}
    details = {r["id"]: r for r in dataset_io.load(CANDIDATES_CSV.replace(".csv", ".jsonl"))}

    records = dataset_io.load("v1")
    ids = {r["id"] for r in records}
    added = skipped = 0
    for rid, row in reviewed.items():
        if row["keep"].strip().lower() not in ("yes", "y"):
            skipped += 1
            continue
        label = row["final_label"].strip() or row["proposed_label"]
        if label not in LABELS:
            print(f"  {rid}: final_label {label!r} is not bug/failed_testcase - skipped")
            skipped += 1
            continue
        if rid in ids:
            continue
        d = details.get(rid, {})
        log, stack = split_log(row["log_excerpt"])
        records.append({
            "id": rid, "framework": row["framework"],
            "log": log, "stacktrace": stack,
            "code_snippet": d.get("_code", ""),
            "description": d.get("_title", ""),
            "label": label, "source": "github",
            "source_ref": row["issue_url"] + " | fix: " + row["fix_url"],
            "split": "",
        })
        added += 1
    dataset_io.save("v1", records)
    print(f"Added {added} reviewed GitHub cases to v1 ({skipped} not kept)")
    print("Next: python -m evaluation.datasets.split --dataset v1")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=20, help="candidates per framework")
    ap.add_argument("--merge", action="store_true", help="add reviewed candidates to v1")
    args = ap.parse_args()
    merge() if args.merge else mine(args.limit)


if __name__ == "__main__":
    main()