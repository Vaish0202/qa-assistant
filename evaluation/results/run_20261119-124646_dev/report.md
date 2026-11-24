# Evaluation: v1 / dev split (n=155)

Cases by source: {'legacy_sample': 30, 'synthetic': 100, 'github': 25} · by label: {'failed_testcase': 78, 'bug': 77}

| Pipeline | Accuracy (95% CI) | Macro-F1 (95% CI) | Bug P / R / F1 | Failed-TC P / R / F1 | p50 time | Unparsed |
|---|---|---|---|---|---:|---:|
| hybrid (ollama:llama3.2) | 71.0% (63.2%–78.1%) | 0.704 (0.625–0.773) | 0.79 / 0.57 / 0.66 | 0.67 / 0.85 / 0.75 | 5.09 s | 0 |

## hybrid (ollama:llama3.2)

| true \ predicted | bug | failed_testcase | unparsed |
|---|---:|---:|---:|
| bug | 44 | 33 | 0 |
| failed_testcase | 12 | 66 | 0 |

| By framework | n | Accuracy | Macro-F1 |
|---|---:|---:|---:|
| api | 30 | 53.3% | 0.525 |
| db | 26 | 73.1% | 0.710 |
| playwright | 32 | 81.2% | 0.750 |
| selenium | 30 | 100.0% | 1.000 |
| unit | 37 | 51.4% | 0.418 |

| By source | n | Accuracy | Macro-F1 |
|---|---:|---:|---:|
| github | 25 | 72.0% | 0.688 |
| legacy_sample | 30 | 73.3% | 0.722 |
| synthetic | 100 | 70.0% | 0.698 |

LLM answered 79 of 155 cases (XGBoost confidence below 0.8).

![confusion matrix](confusion_hybrid.png)

Unparsed LLM answers count as wrong. 95% CIs from 1,000 bootstrap resamples. Groups with small n are indicative only.
