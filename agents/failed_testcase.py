from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from agents.state import AgentState
import json
import re

llm = ChatOllama(model="llama3.2", temperature=0)

SYSTEM_PROMPT = """You are a senior QA engineer. Analyze this failed test case and identify WHY the test itself is failing.

Classify into exactly one of:
- bad_coding_practice: wrong selectors, bad assertions, poor test structure
- locator_relocation: element locators changed, need updating
- awaiting_action: test depends on data/config/environment not ready yet

You MUST respond in this exact JSON only, no other text:
{
  "analysis_type": "bad_coding_practice",
  "severity": "medium",
  "root_cause": "one sentence explanation",
  "suggestions": [
    {"issue": "what is wrong", "fix": "exact fix to apply"}
  ],
  "fixed_code": "corrected version of the test code"
}"""

def failed_testcase_node(state: AgentState) -> AgentState:
    print("--- FAILED TESTCASE AGENT RUNNING ---")

    user_message = f"""
TESTCASE LOGS:
{state['testcase_logs']}

TESTCASE DESCRIPTION:
{state['testcase_description']}

TESTCASE CODE:
{state['testcase_code']}

Analyze why this test is failing and suggest fixes.
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

        state['analysis_type'] = result.get('analysis_type', 'bad_coding_practice')
        state['code_suggestions'] = result.get('suggestions', [])
        state['final_output'] = {
            "type": "failed_testcase",
            "analysis_type": result.get('analysis_type'),
            "severity": result.get('severity', 'medium'),
            "root_cause": result.get('root_cause', ''),
            "suggestions": result.get('suggestions', []),
            "fixed_code": result.get('fixed_code', '')
        }
        print(f"Analysis type: {state['analysis_type']}")

    except json.JSONDecodeError:
        print(f"JSON parse failed. Raw: {raw}")
        state['analysis_type'] = 'bad_coding_practice'
        state['code_suggestions'] = []
        state['final_output'] = {
            "type": "failed_testcase",
            "analysis_type": "bad_coding_practice",
            "severity": "medium",
            "root_cause": "Analysis failed to parse",
            "suggestions": [],
            "fixed_code": ""
        }

    return state