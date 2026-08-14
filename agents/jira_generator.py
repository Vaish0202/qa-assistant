from agents.state import AgentState
import os
from dotenv import load_dotenv
load_dotenv()

def jira_generator_node(state: AgentState) -> AgentState:
    print("--- JIRA GENERATOR AGENT RUNNING ---")

    bug_output = state.get('final_output', {})

    # Prepare Jira payload but DON'T create ticket yet
    # Human approval happens on frontend
    jira_payload = {
        "project_key": os.getenv("JIRA_PROJECT_KEY", "QA"),
        "summary": bug_output.get('summary', 'Bug detected by QA Assistant'),
        "description": bug_output.get('description', ''),
        "bug_type": bug_output.get('bug_type', 'backend'),
        "severity": bug_output.get('severity', 'medium'),
        "steps_to_reproduce": bug_output.get('steps_to_reproduce', []),
        "expected_result": bug_output.get('expected_result', ''),
        "actual_result": bug_output.get('actual_result', ''),
        "suggested_fix": bug_output.get('suggested_fix', '')
    }

    state['jira_payload'] = jira_payload

    # Store payload in final_output for frontend
    state['final_output'] = {
        **bug_output,
        "jira_payload_ready": jira_payload,  # Frontend uses this
        "action": "awaiting_human_approval"   # Signal to frontend
    }

    state['channel_alert'] = f"Bug ready for Jira — awaiting human approval"
    print("Jira payload prepared — waiting for human approval")

    return state