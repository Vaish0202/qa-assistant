from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from agents.state import AgentState
from agents.prompts import BUG_PROMPTS, get_prompt
import json
import re

llm = ChatOllama(model="llama3.2", temperature=0)

def bug_handler_node(state: AgentState) -> AgentState:
    print("--- BUG HANDLER AGENT RUNNING ---")

    framework = state.get('framework', 'default')
    system_prompt = get_prompt(BUG_PROMPTS, framework)

    user_message = f"""
FRAMEWORK: {framework}
TEST TYPE: {state.get('test_type', 'unknown')}
LANGUAGE: {state.get('language', 'python')}

TESTCASE LOGS:
{state['testcase_logs']}

TESTCASE DESCRIPTION:
{state['testcase_description']}

TESTCASE CODE:
{state['testcase_code']}

Analyze this {framework} bug and prepare Jira ticket details.
"""

    messages = [
        SystemMessage(content=system_prompt),
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
            "framework": framework,
            "test_type": state.get('test_type', 'unknown'),
            "language": state.get('language', 'python'),
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
        print(f"Bug type: {state['analysis_type']} | "
              f"Framework: {framework} | "
              f"Severity: {result.get('severity')}")

    except json.JSONDecodeError:
        print(f"JSON parse failed. Raw: {raw}")
        state['analysis_type'] = 'code_bug'
        state['final_output'] = {
            "type": "bug",
            "framework": framework,
            "is_ui_bug": False,
            "bug_type": "backend",
            "severity": "medium",
            "summary": "Bug detected - manual review needed",
            "description": raw[:300] if raw else "",
            "steps_to_reproduce": [],
            "expected_result": "",
            "actual_result": "",
            "suggested_fix": ""
        }

    return state