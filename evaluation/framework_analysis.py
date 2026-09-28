import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sample_data.test_cases import TEST_CASES
from ml_classifier.predict import predict_classification
from agents.framework_detector import detect_framework

# Results from your evaluations
LLM_RESULTS = {
    'TC001': 'failed_testcase', 'TC002': 'failed_testcase',
    'TC003': 'failed_testcase', 'TC004': 'failed_testcase',
    'TC005': 'failed_testcase', 'TC006': 'failed_testcase',
    'TC007': 'failed_testcase', 'TC008': 'failed_testcase',
    'TC009': 'failed_testcase', 'TC010': 'failed_testcase',
    'TC011': 'failed_testcase', 'TC012': 'bug',
    'TC013': 'failed_testcase', 'TC014': 'bug',
    'TC015': 'failed_testcase', 'TC016': 'failed_testcase',
    'TC017': 'bug', 'TC018': 'bug',
    'TC019': 'bug', 'TC020': 'bug',
    'TC021': 'failed_testcase', 'TC022': 'failed_testcase',
    'TC023': 'failed_testcase', 'TC024': 'failed_testcase',
    'TC025': 'failed_testcase', 'TC026': 'failed_testcase',
    'TC027': 'failed_testcase', 'TC028': 'bug',
    'TC029': 'failed_testcase', 'TC030': 'bug'
}

HYBRID_RESULTS = {
    'TC001': 'failed_testcase', 'TC002': 'failed_testcase',
    'TC003': 'bug', 'TC004': 'bug',
    'TC005': 'bug', 'TC006': 'bug',
    'TC007': 'failed_testcase', 'TC008': 'bug',
    'TC009': 'bug', 'TC010': 'bug',
    'TC011': 'bug', 'TC012': 'bug',
    'TC013': 'failed_testcase', 'TC014': 'bug',
    'TC015': 'bug', 'TC016': 'bug',
    'TC017': 'bug', 'TC018': 'bug',
    'TC019': 'failed_testcase', 'TC020': 'bug',
    'TC021': 'bug', 'TC022': 'failed_testcase',
    'TC023': 'bug', 'TC024': 'bug',
    'TC025': 'failed_testcase', 'TC026': 'bug',
    'TC027': 'bug', 'TC028': 'bug',
    'TC029': 'failed_testcase', 'TC030': 'bug'
}

print("="*60)
print("FRAMEWORK-WISE ACCURACY BREAKDOWN")
print("="*60)

frameworks = {}
for tc in TEST_CASES:
    fw = detect_framework(
        tc['testcase_logs'],
        tc['testcase_code'],
        tc['testcase_description']
    )['framework']

    if fw not in frameworks:
        frameworks[fw] = {
            'llm': [], 'xgboost': [], 'hybrid': [], 'expected': []
        }

    xgb = predict_classification(
        tc['testcase_logs'],
        tc['testcase_description'],
        tc['testcase_code']
    )['classification']

    frameworks[fw]['expected'].append(tc['expected'])
    frameworks[fw]['llm'].append(LLM_RESULTS[tc['id']])
    frameworks[fw]['xgboost'].append(xgb)
    frameworks[fw]['hybrid'].append(HYBRID_RESULTS[tc['id']])

print(f"\n{'Framework':<20} {'Count':<8} {'LLM':<10} {'XGBoost':<12} {'Hybrid':<10}")
print("-"*60)

for fw, data in frameworks.items():
    n = len(data['expected'])
    llm_acc = sum(1 for i in range(n) if data['llm'][i] == data['expected'][i]) / n * 100
    xgb_acc = sum(1 for i in range(n) if data['xgboost'][i] == data['expected'][i]) / n * 100
    hyb_acc = sum(1 for i in range(n) if data['hybrid'][i] == data['expected'][i]) / n * 100
    print(f"{fw:<20} {n:<8} {llm_acc:<10.1f} {xgb_acc:<12.1f} {hyb_acc:<10.1f}")

print("\n" + "="*60)
print("OVERALL SUMMARY")
print("="*60)
print(f"Pure LLM    : 21/30 = 70.0% | Avg time: 11.34s")
print(f"Pure XGBoost: 23/30 = 76.7% | Avg time: 0.001s")
print(f"Hybrid      : 23/30 = 76.7% | Avg time: 42.42s")