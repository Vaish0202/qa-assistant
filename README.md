## Observability (LangSmith)

Every analysis is traced end to end. Each of the 5 agents is its own run,
tagged `agent:<name>`, with metadata `run_id`, `pipeline`, `llm_model`,
`framework` and `classification`. `/api/analyze` returns `trace_run_id`.

![Trace tree](docs/images/trace_tree.png)

**Per-agent latency, tokens and cost** (30 benchmark cases, local Ollama llama3.2):

<!-- paste the table from evaluation/results/observability_report.md -->

![Filtered by agent](docs/images/agent_filter.png)

Reproduce: set `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`
in `.env`, then run `python evaluation/trace_report.py`.

## 📄 Research Paper
**QA Assistant: An Agentic AI System for Intelligent 
Test Failure Classification and Automated Bug Diagnosis**

Published on Zenodo — September 2026

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22793445.svg)](https://doi.org/10.5281/zenodo.22793445)