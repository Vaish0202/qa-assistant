"""Agreement numbers for the judge-vs-human check."""
import pytest

from evaluation.generation.human_labels import agreement


def test_perfect_agreement():
    a = agreement([5, 3, 1, 5], [5, 3, 1, 5])
    assert a["exact"] == 1.0 and a["kappa"] == pytest.approx(1.0)


def test_off_by_one_counts_within1():
    a = agreement([5, 4, 3, 2], [4, 4, 2, 2])
    assert a["exact"] == 0.5 and a["within1"] == 1.0
    assert a["weighted_kappa"] > a["kappa"]        # near-misses are penalised less


def test_kappa_undefined_when_everyone_gives_the_same_score():
    a = agreement([5, 5, 5], [5, 5, 5])
    assert a["exact"] == 1.0 and a["kappa"] is None


def test_yes_no_labels():
    a = agreement([True, False, True, False], [True, False, False, False])
    assert a["exact"] == 0.75 and a["within1"] is None
    