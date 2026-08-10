from agents.state import AgentState
from integrations.jira import create_jira_ticket
import os
from dotenv import load_dotenv

load_dotenv()

def jira_generator_node(state: AgentState) -> AgentState:
    print("--- JIRA GENERATOR AGENT RUNNING ---")

    bug_output = state.get('final_output', {})

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
    result = create_jira_ticket(jira_payload)

    if result['success']:
        state['final_output'] = {
            **bug_output,
            "jira_ticket": result['ticket_key'],
            "jira_url": result['ticket_url'],
            "action": "jira_created"
        }
        state['channel_alert'] = f"Jira ticket {result['ticket_key']} created: {result['ticket_url']}"
    else:
        state['final_output'] = {
            **bug_output,
            "jira_error": result.get('error'),
            "action": "jira_failed",
            "jira_payload": jira_payload
        }
        state['channel_alert'] = f"Jira creation failed — manual ticket needed for: {jira_payload['summary']}"

    print(f"Alert: {state['channel_alert']}")
    return state