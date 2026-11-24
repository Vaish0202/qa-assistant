"""The LLM answer parser must read the label however the model formats it."""
from evaluation.predictors import parse_label


def test_clean_json():
    assert parse_label('{"classification": "bug", "confidence": 0.9}') == "bug"


def test_json_with_text_around_it():
    text = 'Sure! Here is my analysis:\n{"classification": "failed_testcase"}\nHope it helps.'
    assert parse_label(text) == "failed_testcase"


def test_broken_json_still_read():
    assert parse_label('{"classification": "bug", "reason": "500 from API",}') == "bug"


def test_plain_text_with_one_label():
    assert parse_label("This is a failed_testcase: the locator is wrong.") == "failed_testcase"


def test_both_labels_mentioned_is_unreadable():
    assert parse_label("It could be a bug or a failed_testcase.") is None


def test_empty_answer():
    assert parse_label("") is None
    assert parse_label(None) is None