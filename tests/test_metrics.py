"""Metrics must give the right numbers on small hand-checked examples."""
import pytest

from evaluation.metrices import (bootstrap_ci, classification_metrics, confusion,
                                group_metrics, mcnemar_p)


def test_perfect_predictions():
    m = classification_metrics(["bug", "failed_testcase"], ["bug", "failed_testcase"])
    assert m["accuracy"] == 1.0
    assert m["macro_f1"] == 1.0


def test_known_values():
    # 3 bugs, 1 failed test; one bug predicted as failed_testcase
    y_true = ["bug", "bug", "bug", "failed_testcase"]
    y_pred = ["bug", "failed_testcase", "bug", "failed_testcase"]
    m = classification_metrics(y_true, y_pred)
    assert m["accuracy"] == 0.75
    assert m["bug"]["precision"] == 1.0                 # 2 of 2 "bug" answers right
    assert m["bug"]["recall"] == pytest.approx(2 / 3)   # found 2 of 3 bugs
    assert m["failed_testcase"]["precision"] == 0.5     # 1 of 2 right
    assert m["failed_testcase"]["recall"] == 1.0
    # bug F1 = 0.8, failed F1 = 2/3
    assert m["macro_f1"] == pytest.approx((0.8 + 2 / 3) / 2)


def test_class_missing_from_sample_is_left_out_of_macro_f1():
    m = classification_metrics(["failed_testcase"] * 3, ["failed_testcase"] * 3)
    assert m["macro_f1"] == 1.0


def test_unparsed_answer_counts_as_wrong():
    m = classification_metrics(["bug", "bug"], ["bug", "unparsed"])
    assert m["accuracy"] == 0.5
    assert confusion(["bug", "bug"], ["bug", "unparsed"])["bug"]["unparsed"] == 1


def test_confusion_counts():
    cm = confusion(["bug", "bug", "failed_testcase"], ["bug", "failed_testcase", "bug"])
    assert cm["bug"] == {"bug": 1, "failed_testcase": 1, "unparsed": 0}
    assert cm["failed_testcase"] == {"bug": 1, "failed_testcase": 0, "unparsed": 0}


def test_bootstrap_interval_contains_the_score():
    y_true = ["bug", "failed_testcase"] * 20
    y_pred = ["bug", "failed_testcase"] * 15 + ["failed_testcase", "bug"] * 5
    score = classification_metrics(y_true, y_pred)["accuracy"]
    lo, hi = bootstrap_ci(y_true, y_pred, "accuracy")
    assert lo <= score <= hi
    assert hi - lo > 0                                   # not a zero-width interval


def test_bootstrap_is_reproducible():
    y_true = ["bug", "failed_testcase", "bug", "bug"] * 5
    y_pred = ["bug", "bug", "bug", "failed_testcase"] * 5
    assert bootstrap_ci(y_true, y_pred) == bootstrap_ci(y_true, y_pred)


def test_mcnemar_identical_pipelines():
    assert mcnemar_p([True, False, True], [True, False, True]) == (1.0, 0, 0)


def test_mcnemar_counts_disagreements():
    p, only_a, only_b = mcnemar_p([True] * 8 + [False] * 2, [False] * 8 + [True] * 2)
    assert (only_a, only_b) == (8, 2)
    assert 0 < p < 1


def test_group_metrics_per_framework():
    records = [{"framework": "api", "label": "bug"},
               {"framework": "api", "label": "failed_testcase"},
               {"framework": "db", "label": "bug"}]
    g = group_metrics(records, ["bug", "bug", "bug"], "framework")
    assert g["api"] == {"n": 2, "accuracy": 0.5, "macro_f1": pytest.approx(1 / 3)}
    assert g["db"]["accuracy"] == 1.0