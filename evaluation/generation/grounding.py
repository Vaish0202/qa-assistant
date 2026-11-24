"""
Rule-based hallucination check: does the output mention specific facts that
are not in the input?

It pulls "checkable facts" out of the output's CLAIMS about the failure
(the Jira summary/description/actual result, or the root cause) and looks
for each one in the log + code + description. Facts it checks:

    exception / error class names   NoSuchElementException, KeyError
    HTTP status codes               404, 500
    quoted strings                  'submit-btn', "toast-success"
    file paths                      tests/ui/test_cart.py

Suggested fixes and improved code are NOT checked: a fix is supposed to
introduce new code (e.g. WebDriverWait), so new names there are expected.

This is deliberately simple and explainable. It complements the LLM judge's
"unsupported_claims" list; neither is perfect on its own.
"""
import re

EXCEPTION = re.compile(r"\b[A-Z][A-Za-z]*(?:Error|Exception)\b")
STATUS = re.compile(r"\b[1-5]\d\d\b")
QUOTED = re.compile(r"""['"`]([^'"`\n]{3,60})['"`]""")
PATH = re.compile(r"\b[\w.-]+(?:/[\w.-]+)+\.(?:py|js|ts|java)\b")

# Generic words that appear in quotes but aren't facts about this failure.
IGNORE = {"bug", "failed_testcase", "high", "medium", "low", "critical",
          "backend", "frontend", "ui", "api", "none", "null", "true", "false"}


def extract_facts(text: str) -> set:
    text = text or ""
    facts = set(EXCEPTION.findall(text)) | set(STATUS.findall(text)) | set(PATH.findall(text))
    facts |= {q.strip() for q in QUOTED.findall(text) if q.strip().lower() not in IGNORE}
    return facts


def unsupported_facts(claims_text: str, source_text: str) -> list:
    """Facts in claims_text that do not appear anywhere in source_text."""
    source = (source_text or "").lower()
    return sorted(f for f in extract_facts(claims_text) if f.lower() not in source)