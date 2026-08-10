from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from agents.state import AgentState
import json
import re

llm = ChatOllama(model="llama3.2", temperature=0)

SYSTEM_PROMPT = """You are a senior software engineer and QA expert.
Given a failing test case, provide specific actionable code fixes.

You MUST respond in this exact JSON only, no other text, no markdown:
{
  "improved_code": "complete corrected test code here as plain string",
  "changes_made": ["change 1", "change 2"],
  "best_practices": ["practice 1", "practice 2"],
  "alternative_approaches": [
    {
      "name": "approach name",
      "code": "alternative code",
      "when_to_use": "scenario"
    }
  ],
  "resources": ["concept or link 1"]
}

IMPORTANT: improved_code must be a plain string, NOT nested JSON."""

def parse_improved_code_field(raw_improved_code: str) -> dict:
    """Handle case where LLM puts JSON inside improved_code field"""
    if not raw_improved_code:
        return {}
    try:
        # If improved_code is itself a JSON string
        inner = json.loads(raw_improved_code)
        if isinstance(inner, dict) and 'improved_code' in inner:
            return inner
    except:
        pass
    return {}

def code_suggestions_node(state: AgentState) -> AgentState:
    print("--- CODE SUGGESTIONS AGENT RUNNING ---")

    current_output = state.get('final_output', {})

    user_message = f"""
ORIGINAL FAILING CODE:
{state['testcase_code']}

TEST LOGS:
{state['testcase_logs']}

ANALYSIS TYPE: {state.get('analysis_type', 'bad_coding_practice')}
ROOT CAUSE: {current_output.get('root_cause', 'Not identified')}

Provide improved code and best practices as plain JSON only.
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

        # Check if improved_code is itself a JSON string (LLM bug)
        improved_code = result.get('improved_code', '')
        changes_made = result.get('changes_made', [])
        best_practices = result.get('best_practices', [])
        alternatives = result.get('alternative_approaches', [])
        resources = result.get('resources', [])

        # If changes_made is empty but improved_code has JSON inside
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
            "improved_code": improved_code,
            "changes_made": changes_made,
            "best_practices": best_practices,
            "alternative_approaches": alternatives,
            "resources": resources,
            "action": "suggestions_provided"
        }
        print(f"Changes: {len(changes_made)}, Alternatives: {len(alternatives)}")

    except json.JSONDecodeError:
        print(f"JSON parse failed. Raw: {raw}")
        state['code_suggestions'] = []
        state['final_output'] = {
            **current_output,
            "improved_code": raw,
            "changes_made": [],
            "best_practices": [],
            "alternative_approaches": [],
            "resources": [],
            "action": "suggestions_provided"
        }

    return state