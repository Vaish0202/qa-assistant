"""
Record format for evaluation datasets (one JSON object per line in vN.jsonl).

    id            unique string, e.g. "syn-0001", "gh-psf-requests-6123", "legacy-TC001"
    framework     one of FRAMEWORKS
    log           test runner output (error message, assertion text)
    stacktrace    stack trace lines ("" if none)
    code_snippet  the failing test code
    description   one line: what the test is supposed to check ("" allowed)
    label         "bug" or "failed_testcase"
    source        where it came from: "legacy_sample", "synthetic", "github", "stackoverflow"
    source_ref    URL, commit or generator name, for traceability ("" allowed)
    split         "dev" or "test" (set by split.py; empty before splitting)
"""

FRAMEWORKS = ["selenium", "playwright", "api", "db", "unit"]
LABELS = ["bug", "failed_testcase"]
SOURCES = ["legacy_sample", "synthetic", "github", "stackoverflow"]
SPLITS = ["dev", "test"]

REQUIRED_FIELDS = ["id", "framework", "log", "stacktrace", "code_snippet",
                   "description", "label", "source", "source_ref", "split"]

# The app's framework detector uses its own names; map them to dataset names.
DETECTOR_TO_DATASET = {
    "selenium": "selenium",
    "playwright": "playwright",
    "pytest_requests": "api",
    "postman": "api",
    "sqlalchemy": "db",
    "pytest": "unit",
    "jest": "unit",
    "junit": "unit",
}