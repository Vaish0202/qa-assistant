# Evaluation: v1 / test split (n=57)

Cases by source: {'synthetic': 50, 'github': 7} · by label: {'bug': 29, 'failed_testcase': 28}

| Pipeline | Accuracy (95% CI) | Macro-F1 (95% CI) | Bug P / R / F1 | Failed-TC P / R / F1 | p50 time | Unparsed |
|---|---|---|---|---|---:|---:|
| xgboost | 63.2% (49.1%–75.4%) | 0.632 (0.491–0.752) | 0.64 / 0.62 / 0.63 | 0.62 / 0.64 / 0.63 | 0.00 s | 0 |

## xgboost

| true \ predicted | bug | failed_testcase | unparsed |
|---|---:|---:|---:|
| bug | 18 | 11 | 0 |
| failed_testcase | 10 | 18 | 0 |

| By framework | n | Accuracy | Macro-F1 |
|---|---:|---:|---:|
| api | 12 | 58.3% | 0.556 |
| db | 11 | 100.0% | 1.000 |
| playwright | 13 | 61.5% | 0.606 |
| selenium | 10 | 50.0% | 0.333 |
| unit | 11 | 45.5% | 0.312 |

| By source | n | Accuracy | Macro-F1 |
|---|---:|---:|---:|
| github | 7 | 85.7% | 0.857 |
| synthetic | 50 | 60.0% | 0.600 |

![confusion matrix](confusion_xgboost.png)

Unparsed LLM answers count as wrong. 95% CIs from 1,000 bootstrap resamples. Groups with small n are indicative only.
