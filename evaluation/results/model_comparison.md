## LLM comparison (v1 dev split, n=3)

| Provider | Model | Accuracy | Macro-F1 | p50 latency | p95 latency | Avg tokens | Cost / 1k classifications | Errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| ollama | `llama3.2` | 100.0% | 0.500 | 37.27 s | 67.86 s | 531 | $0 (local) | 0 |

Same prompt for every model (the classifier agent's framework-specific few-shot prompt), temperature 0. Unreadable answers and API errors count as wrong. Latency is measured from this machine and includes network time. Prices from evaluation/pricing.py.
