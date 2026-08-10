from agents.state import AgentState
from ml_classifier.predict import predict_classification
import os

# Check if model exists, fallback to LLM if not
MODEL_PATH = "ml_classifier/qa_classifier_model.pkl"

def classifier_node(state: AgentState) -> AgentState:
    print("--- CLASSIFIER AGENT RUNNING (ML + LLM Hybrid) ---")

    if os.path.exists(MODEL_PATH):
        # Use fast ML classifier
        result = predict_classification(
            logs=state['testcase_logs'],
            description=state['testcase_description'],
            code=state['testcase_code']
        )
        state['classification'] = result['classification']
        state['classification_confidence'] = result['confidence']
        print(f"ML Classification: {state['classification']} "
              f"({state['classification_confidence']:.2%} confidence)")
        print(f"Bug probability: {result['bug_probability']:.2%}")
        print(f"Failed TC probability: {result['failed_tc_probability']:.2%}")
    else:
        # Fallback to LLM if model not trained yet
        print("ML model not found, falling back to LLM classifier...")
        from langchain_ollama import ChatOllama
        from langchain_core.messages import HumanMessage, SystemMessage
        import json, re

        llm = ChatOllama(model="llama3.2", temperature=0)
        SYSTEM_PROMPT = """Classify as failed_testcase or bug. 
        Return JSON only: {"classification": "...", "confidence": 0.9, "reason": "..."}"""

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"LOGS: {state['testcase_logs']}\nCODE: {state['testcase_code']}")
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