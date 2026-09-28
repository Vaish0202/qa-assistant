import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_classifier.predict import predict_classification
from sample_data.test_cases import TEST_CASES
import time

correct = 0
total = len(TEST_CASES)
results = []

print("="*50)
print("PURE XGBOOST EVALUATION (No LLM)")
print("="*50)

for tc in TEST_CASES:
    start = time.time()
    result = predict_classification(
        tc['testcase_logs'],
        tc['testcase_description'],
        tc['testcase_code']
    )
    elapsed = round(time.time() - start, 4)

    got = result['classification']
    expected = tc['expected']
    is_correct = got == expected
    if is_correct:
        correct += 1

    results.append({
        'id': tc['id'],
        'expected': expected,
        'got': got,
        'correct': is_correct,
        'confidence': result['confidence'],
        'time': elapsed
    })

    print(f"{tc['id']} | Expected: {expected:15} | Got: {got:15} | {'✓' if is_correct else '✗'} | {elapsed}s")

print(f"\nXGBoost Only Accuracy: {correct}/{total} = {(correct/total)*100:.1f}%")
print(f"Average Time: {sum(r['time'] for r in results)/total:.4f}s")