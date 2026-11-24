from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.classifier import classifier_node
from agents.failed_testcase import failed_testcase_node
from agents.bug_handler import bug_handler_node
from agents.jira_generator import jira_generator_node
from agents.code_suggestions import code_suggestions_node
from agents.tracing import traced_agent
from agents.llm import get_model_info
from langsmith import traceable, get_current_run_tree
import os
import uuid

MODEL_PATH = "ml_classifier/qa_classifier_model.pkl"


def route_after_classification(state: AgentState) -> str:
    classification = state.get('classification', 'failed_testcase')
    print(f"--- ROUTER: {classification} | framework={state.get('framework')} ---")
    if classification == 'bug':
        return 'bug_handler'
    return 'failed_testcase_handler'


def build_graph():
    graph = StateGraph(AgentState)
    # Each node is wrapped so it appears in LangSmith as "<name>_agent"
    graph.add_node("classifier", traced_agent("classifier")(classifier_node))
    graph.add_node("failed_testcase_handler",
                   traced_agent("failed_testcase_handler")(failed_testcase_node))
    graph.add_node("bug_handler", traced_agent("bug_handler")(bug_handler_node))
    graph.add_node("jira_generator",
                   traced_agent("jira_generator")(jira_generator_node))
    graph.add_node("code_suggestions",
                   traced_agent("code_suggestions")(code_suggestions_node))
    graph.set_entry_point("classifier")
    graph.add_conditional_edges(
        "classifier",
        route_after_classification,
        {"bug_handler": "bug_handler",
         "failed_testcase_handler": "failed_testcase_handler"}
    )
    graph.add_edge("bug_handler", "jira_generator")
    graph.add_edge("jira_generator", END)
    graph.add_edge("failed_testcase_handler", "code_suggestions")
    graph.add_edge("code_suggestions", END)
    return graph.compile()


qa_graph = build_graph()


def _pipeline_name() -> str:
    """hybrid = XGBoost classifies, LLM writes output; llm_only = LLM does both."""
    return "hybrid_xgboost_llm" if os.path.exists(MODEL_PATH) else "llm_only"


@traceable(name="qa_analysis", run_type="chain")
def _invoke_graph(initial_state: dict) -> dict:
    result = qa_graph.invoke(
        initial_state,
        config={"run_name": "qa_graph",
                "metadata": initial_state["trace_metadata"]},
    )
    # Put the final answer on the root run so you can filter traces by it.
    root = get_current_run_tree()
    if root is not None:
        root.add_metadata({
            "framework": result.get("framework"),
            "classification": result.get("classification"),
            "classification_confidence": result.get("classification_confidence"),
        })
    return result


def run_analysis(
    testcase_logs: str,
    testcase_description: str,
    testcase_code: str,
    user_id: str = "default_user",
    project_id: str = None,
    extra_tags: list = None,        # e.g. ["benchmark"] from evaluation scripts
    extra_metadata: dict = None,    # e.g. {"batch_id": ..., "case_id": ...}
) -> dict:
    run_id = str(uuid.uuid4())
    model_info = get_model_info()
    pipeline = _pipeline_name()
    trace_metadata = {
        "run_id": run_id,
        "pipeline": pipeline,
        "classifier": "xgboost" if pipeline == "hybrid_xgboost_llm" else "llm",
        "llm_provider": model_info["provider"],
        "llm_model": model_info["model"],
        "user_id": user_id,
        **(extra_metadata or {}),
    }

    initial_state: AgentState = {
        "user_id": user_id,
        "project_id": project_id,
        "project_context": None,
        "testcase_logs": testcase_logs,
        "testcase_description": testcase_description,
        "testcase_code": testcase_code,
        "classification": None,
        "classification_confidence": None,
        "analysis_type": None,
        "framework": None,
        "test_type": None,
        "language": None,
        "jira_payload": None,
        "code_suggestions": None,
        "channel_alert": None,
        "final_output": None,
        "trace_metadata": trace_metadata,
    }

    print("\n" + "=" * 50)
    print(f"QA ASSISTANT — STARTING ANALYSIS (run_id={run_id})")
    print("=" * 50)

    result = _invoke_graph(
        initial_state,
        langsmith_extra={
            "run_id": run_id,   # LangSmith trace id == our run_id
            "tags": ["qa-assistant",
                     f"pipeline:{pipeline}",
                     f"llm:{model_info['model']}"] + (extra_tags or []),
            "metadata": trace_metadata,
        },
    )

    print("\n" + "=" * 50)
    print("QA ASSISTANT — COMPLETE")
    print("=" * 50)

    result["trace_run_id"] = run_id
    return result