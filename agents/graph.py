from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.classifier import classifier_node
from agents.failed_testcase import failed_testcase_node
from agents.bug_handler import bug_handler_node
from agents.jira_generator import jira_generator_node
from agents.code_suggestions import code_suggestions_node

def route_after_classification(state: AgentState) -> str:
    classification = state.get('classification', 'failed_testcase')
    print(f"--- ROUTER: classification = {classification} | "
          f"framework = {state.get('framework', 'unknown')} ---")
    if classification == 'bug':
        return 'bug_handler'
    return 'failed_testcase_handler'

def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("classifier", classifier_node)
    graph.add_node("failed_testcase_handler", failed_testcase_node)
    graph.add_node("bug_handler", bug_handler_node)
    graph.add_node("jira_generator", jira_generator_node)
    graph.add_node("code_suggestions", code_suggestions_node)
    graph.set_entry_point("classifier")
    graph.add_conditional_edges(
        "classifier",
        route_after_classification,
        {
            "bug_handler": "bug_handler",
            "failed_testcase_handler": "failed_testcase_handler"
        }
    )
    graph.add_edge("bug_handler", "jira_generator")
    graph.add_edge("jira_generator", END)
    graph.add_edge("failed_testcase_handler", "code_suggestions")
    graph.add_edge("code_suggestions", END)
    return graph.compile()

qa_graph = build_graph()

def run_analysis(
    testcase_logs: str,
    testcase_description: str,
    testcase_code: str,
    user_id: str = "default_user"
) -> dict:
    initial_state: AgentState = {
        "user_id": user_id,
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
        "final_output": None
    }

    print("\n" + "="*50)
    print("QA ASSISTANT — STARTING ANALYSIS")
    print("="*50)

    result = qa_graph.invoke(initial_state)

    print("\n" + "="*50)
    print("QA ASSISTANT — COMPLETE")
    print("="*50)

    return result