from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from agents.state import AgentState
from agents.prompts import FAILED_TC_PROMPTS, get_prompt
import json, re

llm = ChatOllama(model="llama3.2", temperature=0)

def failed_testcase_node(state: AgentState) -> AgentState:
    print("--- FAILED TESTCASE AGENT RUNNING ---")

    framework = state.get('framework', 'default')
    system_prompt = get_prompt(FAILED_TC_PROMPTS, framework)
    project_context = state.get('project_context', '')

    user_message = f"""
{project_context}
FRAMEWORK: {framework}
TEST TYPE: {state.get('test_type', 'unknown')}
LANGUAGE: {state.get('language', 'python')}

TESTCASE LOGS:
{state['testcase_logs']}

TESTCASE DESCRIPTION:
{state['testcase_description']}

TESTCASE CODE:
{state['testcase_code']}

Analyze why this {framework} test is failing.
Give suggestions SPECIFIC to the project tech stack above.
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]

    response = llm.invoke(messages)
    raw = response.content.strip()

    try:
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        result = json.loads(json_match.group() if json_match else raw)

        state['analysis_type'] = result.get('analysis_type', 'bad_coding_practice')
        state['code_suggestions'] = result.get('suggestions', [])
        state['final_output'] = {
            "type": "failed_testcase",
            "framework": framework,
            "test_type": state.get('test_type', 'unknown'),
            "language": state.get('language', 'python'),
            "analysis_type": result.get('analysis_type'),
            "severity": result.get('severity', 'medium'),
            "root_cause": result.get('root_cause', ''),
            "suggestions": result.get('suggestions', []),
            "fixed_code": result.get('fixed_code', '')
        }
        print(f"Analysis: {state['analysis_type']} | Framework: {framework}")

    except json.JSONDecodeError:
        print(f"JSON parse failed. Raw: {raw}")
        state['analysis_type'] = 'bad_coding_practice'
        state['code_suggestions'] = []
        state['final_output'] = {
            "type": "failed_testcase",
            "framework": framework,
            "analysis_type": "bad_coding_practice",
            "severity": "medium",
            "root_cause": raw[:200] if raw else "Could not determine root cause",
            "suggestions": [],
            "fixed_code": ""
        }

    return state