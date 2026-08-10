from agents.state import AgentState
from agents.framework_detector import detect_framework
from agents.prompts import CLASSIFIER_PROMPTS, get_prompt
from ml_classifier.predict import predict_classification
import os

MODEL_PATH = "ml_classifier/qa_classifier_model.pkl"

def classifier_node(state: AgentState) -> AgentState:
    print("--- CLASSIFIER AGENT RUNNING (ML + LLM Hybrid) ---")

    # Step 1: Detect framework
    framework_info = detect_framework(
        state['testcase_logs'],
        state['testcase_code'],
        state['testcase_description']
    )

    # Store framework in state
    state['framework'] = framework_info['framework']
    state['test_type'] = framework_info['test_type']
    state['language'] = framework_info['language']

    # Step 2: ML Classification
    if os.path.exists(MODEL_PATH):
        result = predict_classification(
            logs=state['testcase_logs'],
            description=state['testcase_description'],
            code=state['testcase_code']
        )
        state['classification'] = result['classification']
        state['classification_confidence'] = result['confidence']
        print(f"ML Classification: {state['classification']} "
              f"({state['classification_confidence']:.2%} confidence)")
        print(f"Framework: {framework_info['framework']} "
              f"({framework_info['test_type']}) "
              f"Language: {framework_info['language']}")
    else:
        # Fallback to LLM with framework-specific prompt
        print("ML model not found — using LLM fallback...")
        from langchain_ollama import ChatOllama
        from langchain_core.messages import HumanMessage, SystemMessage
        import json, re

        llm = ChatOllama(model="llama3.2", temperature=0)
        system_prompt = get_prompt(
            CLASSIFIER_PROMPTS,
            framework_info['framework']
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""
FRAMEWORK DETECTED: {framework_info['framework']}
TEST TYPE: {framework_info['test_type']}

LOGS: {state['testcase_logs']}
DESCRIPTION: {state['testcase_description']}
CODE: {state['testcase_code']}
""")
        ]
        response = llm.invoke(messages)
        raw = response.content.strip()
        try:
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            result = json.loads(json_match.group() if json_match else raw)
            state['classification'] = result.get('classification', 'failed_testcase')
            state['classification_confidence'] = result.get('confidence', 0.5)
        except:
            state['classification'] = 'failed_testcase'
            state['classification_confidence'] = 0.5

    return state