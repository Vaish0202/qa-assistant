"""
Classification metrics for the evaluation harness.

Labels are "bug" and "failed_testcase". A prediction that is neither
(e.g. the LLM returned something we could not parse) is counted as
"unparsed": always wrong, and shown as its own column in the confusion matrix.
"""
from collections import defaultdict

import numpy as np

LABELS = ["bug", "failed_testcase"]
UNPARSED = "unparsed"


def classification_metrics(y_true, y_pred):
    """Accuracy, per-class precision/recall/F1/support, and macro-F1."""
    n = len(y_true)
    out = {"n": n,
           "accuracy": sum(t == p for t, p in zip(y_true, y_pred)) / n if n else 0.0}
    f1s = []
    for label in LABELS:
        tp = sum(t == label and p == label for t, p in zip(y_true, y_pred))
        fp = sum(t != label and p == label for t, p in zip(y_true, y_pred))
        fn = sum(t == label and p != label for t, p in zip(y_true, y_pred))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        out[label] = {"precision": precision, "recall": recall, "f1": f1,
                      "support": tp + fn}
        # A class that never appears (not true, not predicted) is left out of
        # macro-F1; otherwise a tiny subgroup with one class scores 0.5 at best.
        if tp + fp + fn:
            f1s.append(f1)
    out["macro_f1"] = float(np.mean(f1s)) if f1s else 0.0
    return out


def bootstrap_ci(y_true, y_pred, metric="macro_f1", n_boot=1000, seed=42):
    """95% confidence interval: resample cases with replacement n_boot times."""
    rng = np.random.default_rng(seed)
    y_true = np.array(y_true, dtype=object)
    y_pred = np.array(y_pred, dtype=object)
    n = len(y_true)
    if n == 0:
        return 0.0, 0.0
    scores = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        scores.append(classification_metrics(list(y_true[idx]), list(y_pred[idx]))[metric])
    lo, hi = np.percentile(scores, [2.5, 97.5])
    return float(lo), float(hi)


def confusion(y_true, y_pred):
    """Rows = true label, columns = predicted label (plus 'unparsed')."""
    cols = LABELS + [UNPARSED]
    return {t: {p: sum(1 for a, b in zip(y_true, y_pred) if a == t and b == p)
                for p in cols}
            for t in LABELS}


def mcnemar_p(correct_a, correct_b):
    """Exact McNemar test on two pipelines' right/wrong answers for the same cases.

    Returns (p_value, only_a_right, only_b_right).
    """
    from scipy.stats import binomtest
    only_a = sum(1 for a, b in zip(correct_a, correct_b) if a and not b)
    only_b = sum(1 for a, b in zip(correct_a, correct_b) if b and not a)
    if only_a + only_b == 0:
        return 1.0, 0, 0
    p = binomtest(min(only_a, only_b), only_a + only_b, 0.5).pvalue
    return float(p), only_a, only_b


def group_metrics(records, preds, key):
    """Accuracy and macro-F1 per group, e.g. key='framework' or key='source'."""
    groups = defaultdict(lambda: ([], []))
    for record, pred in zip(records, preds):
        groups[record[key]][0].append(record["label"])
        groups[record[key]][1].append(pred)
    result = {}
    for name, (t, p) in sorted(groups.items()):
        m = classification_metrics(t, p)
        result[name] = {"n": len(t), "accuracy": m["accuracy"], "macro_f1": m["macro_f1"]}
    return result