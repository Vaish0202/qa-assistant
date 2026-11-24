## Observability report (batch `bench-e390b142`)

Traces: 3 · LLM: llama3.2

| Agent | Runs | p50 latency | p95 latency | Avg prompt tokens | Avg completion tokens | Actual cost / run | Est. cost on openai/gpt-oss-20b / run |
|---|---:|---:|---:|---:|---:|---:|---:|
| bug_handler | 1 | 70.22 s | 70.22 s | 290 | 196 | $0.000000 | $0.000081 |
| classifier | 3 | 0.42 s | 5.30 s | 0 | 0 | $0.000000 | $0.000000 |
| code_suggestions | 2 | 112.63 s | 136.85 s | 314 | 237 | $0.000000 | $0.000095 |
| failed_testcase_handler | 2 | 82.34 s | 123.16 s | 375 | 86 | $0.000000 | $0.000054 |
| jira_generator | 1 | 0.00 s | 0.00 s | 0 | 0 | $0.000000 | $0.000000 |

- End-to-end latency: p50 128.65 s, p95 258.83 s
- XGBoost classifier: p50 348.9 ms, p95 4834.6 ms
- Tokens per classification: 837
- Cost per classification: $0.000000 actual, $0.000126 estimated on openai/gpt-oss-20b (≈ $0.13 per 1,000)

Latency is wall-clock time per agent run, including the LLM call. Bug-path agents (bug_handler, jira_generator) and failed-test-path agents (failed_testcase_handler, code_suggestions) only run for their own cases, so their run counts are lower than the classifier's.
