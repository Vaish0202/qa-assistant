"""
LangSmith tracing helpers.

Tracing is switched on purely by environment variables
(LANGSMITH_TRACING=true + LANGSMITH_API_KEY). When they are not set,
these decorators do nothing, so the app runs exactly as before.

Each agent gets:
  - a run named "<agent>_agent"
  - the tag "agent:<agent>"   (filter one agent in the LangSmith UI)
  - metadata: agent, run_id, pipeline, classifier, llm_provider, llm_model,
              framework, classification, confidence
"""
import functools
from dotenv import load_dotenv
from langsmith import traceable, get_current_run_tree

load_dotenv()


def _metadata_from_state(state: dict) -> dict:
    """Run-level metadata (run_id, pipeline, model) plus what is known so far."""
    meta = dict(state.get("trace_metadata") or {})
    for key in ("framework", "classification", "classification_confidence",
                "analysis_type", "test_type"):
        value = state.get(key)
        if value is not None:
            meta[key] = value
    return meta


def traced_agent(agent_name: str):
    """Wrap a LangGraph node so it shows up as its own tagged run."""
    def decorator(node_fn):
        @traceable(
            name=f"{agent_name}_agent",
            run_type="chain",
            tags=[f"agent:{agent_name}"],
            metadata={"agent": agent_name},
        )
        def _traced(state):
            run = get_current_run_tree()
            if run is not None:
                run.add_metadata(_metadata_from_state(state))

            new_state = node_fn(state)

            # The classifier only learns framework/classification while it runs,
            # so add them again on the way out.
            if run is not None:
                run.add_metadata(_metadata_from_state(new_state))
            return new_state

        @functools.wraps(node_fn)
        def wrapper(state):
            return _traced(state)

        return wrapper
    return decorator