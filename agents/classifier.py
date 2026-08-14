from agents.llm import get_llm
from agents.state import AgentState
from agents.framework_detector import detect_framework
from agents.prompts import CLASSIFIER_PROMPTS, get_prompt
from agents.project_context import get_project_context
from ml_classifier.predict import predict_classification
import os

MODEL_PATH = "ml_classifier/qa_classifier_model.pkl"

def classifier_node(state: AgentState) -> AgentState:
    print("--- CLASSIFIER AGENT RUNNING (ML + LLM Hybrid) ---")

    # Step 1: Get project context if available
    project_data = get_project_context(state.get('project_id'))
    state['project_context'] = project_data['context_string']

    if project_data['project']:
        print(f"Project: {project_data['project']['name']}")

    # Step 2: Detect framework
    framework_info = detect_framework(
        state['testcase_logs'],
        state['testcase_code'],
        state['testcase_description']
    )

    # Override framework from project if available
    if project_data['project'] and project_data['project']['test_framework']:
        project_framework = project_data['project']['test_framework']
        if project_framework in ['selenium', 'pytest_requests', 'sqlalchemy', 'jest', 'junit']:
            framework_info['framework'] = project_framework
            print(f"Framework overridden by project: {project_framework}")

    state['framework'] = framework_info['framework']
    state['test_type'] = framework_info['test_type']
    state['language'] = framework_info['language']

    # Step 3: ML Classification
    if os.path.exists(MODEL_PATH):
        result = predict_classification(
            logs=state['testcase_logs'],
            description=state['testcase_description'],
            code=state['testcase_code']
        )
        state['classification'] = result['classification']
        state['classification_confidence'] = result['confidence']
        print(f"ML Classification: {state['classification']} "
              f"({state['classification_confidence']:.2%})")
    else:
        from agents.llm import get_llm
        from langchain_core.messages import HumanMessage, SystemMessage
        import json, re

        
        llm = get_llm()
        system_prompt = get_prompt(CLASSIFIER_PROMPTS, framework_info['framework'])
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""
{state.get('project_context', '')}
FRAMEWORK: {framework_info['framework']}
LOGS: {state['testcase_logs']}
CODE: {state['testcase_code']}
""")
        ]
        response = llm.invoke(messages)
        raw = response.content.strip()
        try:
            json_match = __import__('re').search(r'\{.*\}', raw, __import__('re').DOTALL)
            result = json.loads(json_match.group() if json_match else raw)
            state['classification'] = result.get('classification', 'failed_testcase')
            state['classification_confidence'] = result.get('confidence', 0.5)
        except:
            state['classification'] = 'failed_testcase'
            state['classification_confidence'] = 0.5

    return state