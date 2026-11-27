# Evaluation: v1 / test split (n=47)

Cases by source: {'synthetic': 40, 'github': 7}  ·  by label: {'bug': 24, 'failed_testcase': 23}

| Pipeline | Accuracy (95% CI) | Macro-F1 (95% CI) | Bug P / R | Failed-TC P / R | p50 time | LLM calls |
|---|---|---|---|---|---:|---:|
| xgboost | 72.3% (57.4%–85.1%) | 0.721 (0.573–0.850) | 0.79 / 0.62 | 0.68 / 0.83 | 0.00 s | 0 |

## xgboost

| By framework | n | Accuracy | Macro-F1 |
|---|---:|---:|---:|
| api | 10 | 60.0% | 0.583 |
| db | 9 | 100.0% | 1.000 |
| playwright | 11 | 63.6% | 0.633 |
| selenium | 8 | 100.0% | 1.000 |
| unit | 9 | 44.4% | 0.308 |

| By source | n | Accuracy | Macro-F1 |
|---|---:|---:|---:|
| github | 7 | 85.7% | 0.857 |
| synthetic | 40 | 70.0% | 0.697 |

![confusion matrix](confusion_xgboost.png)

Notes: unreadable LLM answers count as wrong. Macro-F1 averages only the classes present in the sample. 95% CIs from 1,000 bootstrap resamples. Groups with small n are indicative only.
