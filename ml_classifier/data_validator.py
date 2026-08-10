import json
from ml_classifier.feature_extractor import extract_features
import numpy as np

REQUIRED_KEYS = ['logs', 'description', 'code', 'label']
VALID_LABELS = ['bug', 'failed_testcase']

def validate_single(item: dict, index: int) -> tuple:
    """Validate a single training example. Returns (is_valid, error_message)"""
    
    # Check required keys
    for key in REQUIRED_KEYS:
        if key not in item:
            return False, f"Missing key: '{key}'"
    
    # Check label
    if item['label'] not in VALID_LABELS:
        return False, f"Invalid label: '{item['label']}' — must be 'bug' or 'failed_testcase'"
    
    # Check non-empty
    if not item['logs'].strip():
        return False, "logs field is empty"
    if not item['description'].strip():
        return False, "description field is empty"
    if not item['code'].strip():
        return False, "code field is empty"
    
    # Check minimum length
    if len(item['logs']) < 10:
        return False, f"logs too short ({len(item['logs'])} chars) — paste actual error log"
    
    # Check features extractable
    try:
        features = extract_features(item['logs'], item['description'], item['code'])
        if np.all(features == 0):
            return False, "All features are zero — logs/code may not contain recognizable patterns"
    except Exception as e:
        return False, f"Feature extraction failed: {str(e)}"
    
    return True, "OK"

def validate_dataset(data: list, dataset_name: str = "dataset") -> dict:
    """Validate entire dataset and return report"""
    
    print(f"\n{'='*50}")
    print(f"VALIDATING: {dataset_name}")
    print(f"Total examples: {len(data)}")
    print(f"{'='*50}")
    
    valid = []
    invalid = []
    bug_count = 0
    failed_tc_count = 0
    
    for i, item in enumerate(data):
        is_valid, message = validate_single(item, i)
        if is_valid:
            valid.append(item)
            if item['label'] == 'bug':
                bug_count += 1
            else:
                failed_tc_count += 1
        else:
            invalid.append({'index': i, 'error': message, 'item': item})
            print(f"  ✗ Example {i}: {message}")
    
    print(f"\n✓ Valid examples: {len(valid)}")
    print(f"✗ Invalid examples: {len(invalid)}")
    print(f"  Bug examples: {bug_count}")
    print(f"  Failed TC examples: {failed_tc_count}")
    
    # Check balance
    if len(valid) > 0:
        ratio = bug_count / len(valid)
        if ratio < 0.3:
            print(f"\n⚠️  WARNING: Dataset imbalanced — only {ratio:.0%} bugs")
            print("   Add more bug examples for better training")
        elif ratio > 0.7:
            print(f"\n⚠️  WARNING: Dataset imbalanced — {ratio:.0%} bugs")
            print("   Add more failed_testcase examples")
        else:
            print(f"\n✓ Dataset balance OK: {ratio:.0%} bugs, {1-ratio:.0%} failed_tc")
    
    return {
        'valid': valid,
        'invalid': invalid,
        'bug_count': bug_count,
        'failed_tc_count': failed_tc_count,
        'total_valid': len(valid)
    }

if __name__ == "__main__":
    from ml_classifier.training_data import TRAINING_DATA
    report = validate_dataset(TRAINING_DATA, "Synthetic Training Data")