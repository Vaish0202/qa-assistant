from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from agents.state import AgentState
import json
import re

llm = ChatOllama(model="llama3.2", temperature=0)

SYSTEM_PROMPT = """You are a senior QA engineer. A test has revealed a real bug in the application.

Determine if this is a UI bug or a backend/logic bug.

You MUST respond in this exact JSON only, no other text:
{
  "is_ui_bug": false,
  "bug_type": "backend",
  "severity": "high",
  "summary": "short one-line bug title for Jira",
  "description": "detailed bug description",
  "steps_to_reproduce": ["step 1", "step 2"],
  "expected_result": "what should happen",
  "actual_result": "what actually happened",
  "suggested_fix": "developer hint"
}"""

def bug_handler_node(state: AgentState) -> AgentState:
    print("--- BUG HANDLER AGENT RUNNING ---")

    user_message = f"""
TESTCASE LOGS:
{state['testcase_logs']}

TESTCASE DESCRIPTION:
{state['testcase_description']}

TESTCASE CODE:
{state['testcase_code']}

Analyze this bug and prepare Jira ticket details.
"""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message)
    ]

    response = llm.invoke(messages)
    raw = response.content.strip()

    try:
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(raw)

        is_ui_bug = result.get('is_ui_bug', False)
        state['analysis_type'] = 'ui_bug' if is_ui_bug else 'code_bug'
        state['final_output'] = {
            "type": "bug",
            "is_ui_bug": is_ui_bug,
            "bug_type": result.get('bug_type', 'backend'),
            "severity": result.get('severity', 'medium'),
            "summary": result.get('summary', ''),
            "description": result.get('description', ''),
            "steps_to_reproduce": result.get('steps_to_reproduce', []),
            "expected_result": result.get('expected_result', ''),
            "actual_result": result.get('actual_result', ''),
            "suggested_fix": result.get('suggested_fix', '')
        }
        print(f"Bug type: {state['analysis_type']}, Severity: {result.get('severity')}")

    except json.JSONDecodeError:
        print(f"JSON parse failed. Raw: {raw}")
        state['analysis_type'] = 'code_bug'
        state['final_output'] = {
            "type": "bug",
            "is_ui_bug": False,
            "bug_type": "backend",
            "severity": "medium",
            "summary": "Bug detected - manual review needed",
            "description": raw,
            "steps_to_reproduce": [],
            "expected_result": "",
            "actual_result": "",
            "suggested_fix": ""
        }

    return state