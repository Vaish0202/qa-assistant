# Evaluation: v1 / dev split (n=155)

Cases by source: {'legacy_sample': 30, 'synthetic': 100, 'github': 25} · by label: {'failed_testcase': 78, 'bug': 77}

| Pipeline | Accuracy (95% CI) | Macro-F1 (95% CI) | Bug P / R / F1 | Failed-TC P / R / F1 | p50 time | Unparsed |
|---|---|---|---|---|---:|---:|
| hybrid (ollama:llama3.2) | 71.6% (63.9%–78.7%) | 0.712 (0.637–0.780) | 0.78 / 0.60 / 0.68 | 0.68 / 0.83 / 0.75 | 0.09 s | 0 |

## hybrid (ollama:llama3.2)

| true \ predicted | bug | failed_testcase | unparsed |
|---|---:|---:|---:|
| bug | 46 | 31 | 0 |
| failed_testcase | 13 | 65 | 0 |

| By framework | n | Accuracy | Macro-F1 |
|---|---:|---:|---:|
| api | 30 | 46.7% | 0.464 |
| db | 26 | 73.1% | 0.710 |
| playwright | 32 | 96.9% | 0.965 |
| selenium | 30 | 83.3% | 0.824 |
| unit | 37 | 59.5% | 0.563 |

| By source | n | Accuracy | Macro-F1 |
|---|---:|---:|---:|
| github | 25 | 64.0% | 0.571 |
| legacy_sample | 30 | 83.3% | 0.833 |
| synthetic | 100 | 70.0% | 0.698 |

LLM answered 55 of 155 cases (XGBoost confidence below 0.7).

![confusion matrix](confusion_hybrid.png)

Unparsed LLM answers count as wrong. 95% CIs from 1,000 bootstrap resamples. Groups with small n are indicative only.
