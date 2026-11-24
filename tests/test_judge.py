"""Hallucination rule check and judge-answer parsing."""
from evaluation.generation.grounding import extract_facts, unsupported_facts
from evaluation.generation.judge import parse_judgment

LOG = ('selenium.common.exceptions.NoSuchElementException: no such element: '
       '[id="submit_btn"]\nFAILED tests/ui/test_login.py::test_login')


def test_facts_found_in_text():
    facts = extract_facts("NoSuchElementException for 'submit_btn' in tests/ui/test_login.py, got 404")
    assert {"NoSuchElementException", "submit_btn", "tests/ui/test_login.py", "404"} <= facts


def test_supported_claim_is_not_flagged():
    assert unsupported_facts("Locator 'submit_btn' raised NoSuchElementException", LOG) == []


def test_invented_facts_are_flagged():
    claims = "The API returned 500 and a NullPointerException in 'checkout-service'"
    assert unsupported_facts(claims, LOG) == ["500", "NullPointerException", "checkout-service"]


def test_generic_quoted_words_are_ignored():
    assert unsupported_facts("Severity 'high', type 'bug'", LOG) == []


def test_parse_valid_judgment():
    j = parse_judgment('Sure: {"correctness": 4, "groundedness": "5", "actionability": 3.4, '
                       '"unsupported_claims": []}')
    assert (j["correctness"], j["groundedness"], j["actionability"]) == (4, 5, 3)
    assert j["unsupported_claims"] == []


def test_out_of_range_or_missing_score_is_rejected():
    assert parse_judgment('{"correctness": 7, "groundedness": 5, "actionability": 3}') is None
    assert parse_judgment('{"correctness": 4, "groundedness": 5}') is None
    assert parse_judgment("no json here") is None