import re

FRAMEWORKS = {
    "selenium": {
        "keywords": ["webdriver", "driver.", "find_element", "by.id", "by.xpath", 
                    "by.css", "webdriverwait", "expected_conditions", "actionchains",
                    "driver.get(", "driver.find", "send_keys", "driver.quit"],
        "error_patterns": ["nosuchelementexception", "timeoutexception", 
                          "staleelementreferenceexception", "elementclickintercepted",
                          "elementnotinteractable", "nosuchwindowexception"],
        "language": "python",
        "type": "ui"
    },
    "pytest_requests": {
        "keywords": ["requests.get", "requests.post", "requests.put", "requests.delete",
                    "response.status_code", "response.json()", "requests.patch",
                    "assert response", "r.status_code", "r.json()"],
        "error_patterns": ["assertionerror: assert", "status_code", "connectionerror",
                          "httperror", "connectionrefused", "jsondecodeerror"],
        "language": "python",
        "type": "api"
    },
    "sqlalchemy": {
        "keywords": ["db.query", "session.query", "db.commit", "session.commit",
                    "db.add(", "session.add(", "sqlalchemy", "db.execute",
                    "filter_by(", "db.delete", "Base.metadata"],
        "error_patterns": ["integrityerror", "operationalerror", "no such table",
                          "unique constraint", "foreign key", "sqlalchemy"],
        "language": "python",
        "type": "database"
    },
    "pytest": {
        "keywords": ["def test_", "@pytest.fixture", "pytest.raises", "conftest",
                    "parametrize", "pytest.mark", "assert ", "setup_method"],
        "error_patterns": ["failed", "error", "assertionerror", "fixture"],
        "language": "python",
        "type": "unit"
    },
    "jest": {
        "keywords": ["describe(", "it(", "test(", "expect(", "toBe(", "toEqual(",
                    "beforeEach(", "afterEach(", "jest.mock(", "render(", "screen."],
        "error_patterns": ["expect(", "received", "tobeinthedo", "jest"],
        "language": "javascript",
        "type": "unit"
    },
    "junit": {
        "keywords": ["@test", "@before", "@after", "assertequals", "asserttrue",
                    "assertfalse", "assertnotnull", "junit", "@runwith", "mockito"],
        "error_patterns": ["assertionerror", "junit", "java.lang", "nullpointerexception"],
        "language": "java",
        "type": "unit"
    },
    "postman": {
        "keywords": ["pm.test", "pm.response", "pm.expect", "postman", 
                    "pm.environment", "pm.globals"],
        "error_patterns": ["assertionerror", "test failed", "pm.test"],
        "language": "javascript",
        "type": "api"
    }
}

def detect_framework(logs: str, code: str, description: str) -> dict:
    """
    Detect testing framework from logs, code and description.
    Returns framework info dict.
    """
    logs_lower = logs.lower()
    code_lower = code.lower()
    desc_lower = description.lower()
    combined = f"{logs_lower} {code_lower} {desc_lower}"

    scores = {}

    for framework, info in FRAMEWORKS.items():
        score = 0

        # Check keywords in code (highest weight)
        for kw in info["keywords"]:
            if kw.lower() in code_lower:
                score += 3

        # Check error patterns in logs (high weight)
        for pattern in info["error_patterns"]:
            if pattern.lower() in logs_lower:
                score += 2

        # Check in description (low weight)
        if framework in desc_lower:
            score += 1

        scores[framework] = score

    # Get best match
    best_framework = max(scores, key=scores.get)
    best_score = scores[best_framework]

    # If no clear match default to pytest
    if best_score == 0:
        best_framework = "pytest"
        confidence = 0.3
    else:
        total = sum(scores.values())
        confidence = best_score / total if total > 0 else 0.5

    framework_info = FRAMEWORKS[best_framework]

    result = {
        "framework": best_framework,
        "language": framework_info["language"],
        "test_type": framework_info["type"],
        "confidence": round(confidence, 2),
        "all_scores": scores
    }

    print(f"Framework detected: {best_framework} ({framework_info['type']}) "
          f"confidence: {confidence:.0%}")

    return result