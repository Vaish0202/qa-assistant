import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sample_data.test_cases import TEST_CASES
from ml_classifier.predict import predict_classification
from agents.framework_detector import detect_framework
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
import re, json, time

llm = ChatOllama(model="llama3.2", temperature=0)

SYSTEM_PROMPT = """You are a QA expert. Classify as failed_testcase or bug.
Respond ONLY in JSON: {"classification": "...", "confidence": 0.0-1.0}"""

def llm_classify(logs, desc, code):
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"LOGS: {logs}\nDESC: {desc}\nCODE: {code}")
    ]
    response = llm.invoke(messages)
    try:
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        result = json.loads(match.group())
        return result.get('classification', 'failed_testcase')
    except:
        return 'failed_testcase'

def adaptive_classify(logs, desc, code):
    fw = detect_framework(logs, code, desc)['framework']
    if fw in ['selenium', 'pytest']:
        return predict_classification(logs, desc, code)['classification'], fw, 'xgboost'
    else:
        return llm_classify(logs, desc, code), fw, 'llm'

correct = 0
total = len(TEST_CASES)
print("="*50)
print("ADAPTIVE CLASSIFIER EVALUATION")
print("="*50)

for tc in TEST_CASES:
    got, fw, method = adaptive_classify(
        tc['testcase_logs'],
        tc['testcase_description'],
        tc['testcase_code']
    )
    expected = tc['expected']
    is_correct = got == expected
    if is_correct:
        correct += 1
    print(f"{tc['id']} | {fw:15} | {method:8} | "
          f"{'✓' if is_correct else '✗'} | {got}")

print(f"\nAdaptive Accuracy: {correct}/{total} = {correct/total*100:.1f}%")
