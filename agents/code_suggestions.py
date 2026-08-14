
from langchain_core.messages import HumanMessage, SystemMessage
from agents.state import AgentState
from agents.prompts import CODE_SUGGESTION_PROMPTS, get_prompt
import json
import re

from agents.llm import get_llm
llm = get_llm()

def parse_improved_code_field(raw_improved_code: str) -> dict:
    if not raw_improved_code:
        return {}
    try:
        inner = json.loads(raw_improved_code)
        if isinstance(inner, dict) and 'improved_code' in inner:
            return inner
    except:
        pass
    return {}

def code_suggestions_node(state: AgentState) -> AgentState:
    print("--- CODE SUGGESTIONS AGENT RUNNING ---")

    framework = state.get('framework', 'default')
    current_output = state.get('final_output', {})
    system_prompt = get_prompt(CODE_SUGGESTION_PROMPTS, framework)

    user_message = f"""
FRAMEWORK: {framework}
TEST TYPE: {state.get('test_type', 'unknown')}
LANGUAGE: {state.get('language', 'python')}

ORIGINAL FAILING CODE:
{state['testcase_code']}

TEST LOGS:
{state['testcase_logs']}

ANALYSIS TYPE: {state.get('analysis_type', 'bad_coding_practice')}
ROOT CAUSE: {current_output.get('root_cause', 'Not identified')}

Provide {framework}-specific improved code and best practices.
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

        improved_code = result.get('improved_code', '')
        changes_made = result.get('changes_made', [])
        best_practices = result.get('best_practices', [])
        alternatives = result.get('alternative_approaches', [])
        resources = result.get('resources', [])

        # Handle nested JSON in improved_code
        if not changes_made and improved_code:
            inner = parse_improved_code_field(improved_code)
            if inner:
                improved_code = inner.get('improved_code', improved_code)
                changes_made = inner.get('changes_made', [])
                best_practices = inner.get('best_practices', [])
                alternatives = inner.get('alternative_approaches', [])
                resources = inner.get('resources', [])

        state['code_suggestions'] = alternatives
        state['final_output'] = {
            **current_output,
            "framework": framework,
            "improved_code": improved_code,
            "changes_made": changes_made,
            "best_practices": best_practices,
            "alternative_approaches": alternatives,
            "resources": resources,
            "action": "suggestions_provided"
        }
        print(f"Framework: {framework} | "
              f"Changes: {len(changes_made)} | "
              f"Alternatives: {len(alternatives)}")

    except json.JSONDecodeError:
        print(f"JSON parse failed. Raw: {raw}")
        state['code_suggestions'] = []
        state['final_output'] = {
            **current_output,
            "framework": framework,
            "improved_code": raw,
            "changes_made": [],
            "best_practices": [],
            "alternative_approaches": [],
            "resources": [],
            "action": "suggestions_provided"
        }

    return state