#!/usr/bin/env python3
"""
Build a QA dataset (logs / description / code / label / source) from
Stack Overflow question URLs using the official Stack Exchange API.

Setup:
    pip install requests beautifulsoup4

Usage:
    1. Put one Stack Overflow question URL per line in urls.txt
    2. python so_to_dataset.py urls.txt dataset.json

Notes:
    - Text is copied verbatim from the question body (code blocks only).
    - "description" and "label" are left empty on purpose: fill them in
      after reading each question. "_title" is a helper to make that easy;
      delete it before training if you don't want it.
    - Without an API key the limit is ~300 requests/day, which is plenty
      because up to 100 questions are fetched per request.
"""

import json
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

API_URL = "https://api.stackexchange.com/2.3/questions/{ids}"
ID_RE = re.compile(r"stackoverflow\.com/(?:questions|q)/(\d+)")

# Heuristic: score each block line by line. Lines that look like error output
# count as log lines, lines that look like source code count as code lines.
LOG_LINE = re.compile(
    r"^\s*("
    r"Traceback \(most recent call last\)"
    r"|File \".*\", line \d+"
    r"|-+>\s*\d+"
    r"|[\w.]+(Exception|Error)\b.*:"
    r"|Exception in thread"
    r"|at [\w.$<>]+\(.*\)"
    r"|FAILED|FAIL:|ERROR\b|npm ERR!|AssertionError"
    r"|~/.*\bin\b"
    r")"
)
CODE_LINE = re.compile(
    r"^\s*("
    r"def |class |import |from \S+ import |try:|except\b|catch\b|using\b|var "
    r"|public |private |if\s*\(|for\s*\(|return\b|driver\.|[\w.\[\]]+\s*=\s*"
    r")"
)


def read_ids(path):
    ids = []
    total_lines = duplicates = skipped = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            total_lines += 1
            found = ID_RE.findall(line)  # every URL on the line, not just the first
            if not found:
                skipped += 1
                print(f"Skipping line (no question ID found): {line.strip()}")
            for qid in found:
                if qid in ids:
                    duplicates += 1
                else:
                    ids.append(qid)
    print(
        f"Read {total_lines} non-empty lines: {len(ids)} unique question IDs, "
        f"{duplicates} duplicates, {skipped} lines skipped"
    )
    return ids


def fetch_questions(ids):
    """Fetch question bodies in batches of up to 100 IDs."""
    items = []
    for i in range(0, len(ids), 100):
        batch = ids[i : i + 100]
        page = 1
        while True:
            # The API returns only 30 results per page unless pagesize is set,
            # so ask for 100 and keep going while has_more is true.
            resp = requests.get(
                API_URL.format(ids=";".join(batch)),
                params={
                    "site": "stackoverflow",
                    "filter": "withbody",
                    "pagesize": 100,
                    "page": page,
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            items.extend(data.get("items", []))
            if data.get("backoff"):
                print(f"API asked us to back off for {data['backoff']}s")
                time.sleep(data["backoff"])
            if not data.get("has_more"):
                break
            page += 1
    return items


def split_blocks(html_body):
    """Return (logs, code) text taken from <pre> blocks of the question body."""
    soup = BeautifulSoup(html_body, "html.parser")
    logs, code = [], []
    for pre in soup.find_all("pre"):
        text = pre.get_text().strip("\n")
        if not text.strip():
            continue
        lines = text.splitlines()
        log_score = sum(1 for ln in lines if LOG_LINE.match(ln))
        code_score = sum(1 for ln in lines if CODE_LINE.match(ln))
        (logs if log_score > 0 and log_score >= code_score else code).append(text)
    return "\n\n".join(logs), "\n\n".join(code)


def build_entry(item):
    logs, code = split_blocks(item.get("body", ""))
    qid = item["question_id"]
    return {
        "logs": logs,
        "description": "",  # fill in: one sentence on what the test does
        "code": code,
        "label": "",  # fill in: failed_testcase OR bug
        "source": f"stackoverflow.com/questions/{qid}",
        "_title": item.get("title", ""),  # helper, optional to keep
        # True when logs or code is empty: the error text may be in the prose
        "_needs_review": not logs or not code,
    }


def main():
    if len(sys.argv) != 3:
        print("Usage: python so_to_dataset.py urls.txt dataset.json")
        sys.exit(1)

    ids = read_ids(sys.argv[1])
    if not ids:
        print("No valid Stack Overflow question URLs found.")
        sys.exit(1)

    items = fetch_questions(ids)
    found = {str(it["question_id"]) for it in items}
    for qid in ids:
        if qid not in found:
            print(
                "Not returned by API (deleted, merged or not a question ID?): "
                f"https://stackoverflow.com/q/{qid}"
            )

    dataset = [build_entry(it) for it in items]
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(dataset)} entries to {sys.argv[2]}")


if __name__ == "__main__":
    main()