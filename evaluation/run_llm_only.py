import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from sample_data.test_cases import TEST_CASES
import json
import re
import time
import csv
from datetime import datetime

llm = ChatOllama(model="llama3.2", temperature=0)

SYSTEM_PROMPT = """You are a QA expert classifying software test failures.
RULES:
- failed_testcase: TEST CODE is wrong
- bug: APPLICATION behaves incorrectly

Respond ONLY in JSON:
{"classification": "...", "confidence": 0.0-1.0, "reason": "..."}"""

def classify_with_llm(logs, description, code):
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"""
LOGS: {logs}
DESCRIPTION: {description}
CODE: {code}
Classify this issue.
""")
    ]
    response = llm.invoke(messages)
    raw = response.content.strip()
    try:
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        result = json.loads(json_match.group() if json_match else raw)
        return result.get('classification', 'failed_testcase'), result.get('confidence', 0.5)
    except:
        return 'failed_testcase', 0.5

results = []
correct = 0
total = len(TEST_CASES)

print("="*50)
print("PURE LLM EVALUATION (No ML)")
print(f"Total cases: {total}")
print("="*50)

for tc in TEST_CASES:
    start = time.time()
    got, confidence = classify_with_llm(
        tc['testcase_logs'],
        tc['testcase_description'],
        tc['testcase_code']
    )
    elapsed = round(time.time() - start, 2)
    expected = tc['expected']
    is_correct = got == expected
    if is_correct:
        correct += 1

    results.append({
        'id': tc['id'],
        'expected': expected,
        'got': got,
        'correct': is_correct,
        'confidence': round(confidence, 2),
        'time': elapsed
    })

    print(f"{tc['id']} | Expected: {expected:15} | Got: {got:15} | {'✓' if is_correct else '✗'} | {elapsed}s")

accuracy = round((correct/total)*100, 1)
avg_time = round(sum(r['time'] for r in results)/total, 2)

print(f"\nPure LLM Accuracy: {correct}/{total} = {accuracy}%")
print(f"Average Time: {avg_time}s")

# Save CSV
filename = f"evaluation/llm_only_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
with open(filename, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['id','expected','got','correct','confidence','time'])
    writer.writeheader()
    writer.writerows(results)
print(f"Saved: {filename}")