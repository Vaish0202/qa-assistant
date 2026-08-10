from ml_classifier.training_data import TRAINING_DATA
from ml_classifier.real_data import REAL_DATA
from ml_classifier.data_validator import validate_dataset

def merge_and_prepare():
    """Merge synthetic + real data, validate, return clean dataset"""
    
    print("MERGING DATASETS")
    print(f"Synthetic examples: {len(TRAINING_DATA)}")
    print(f"Real examples: {len(REAL_DATA)}")
    
    # Validate synthetic data
    synthetic_report = validate_dataset(TRAINING_DATA, "Synthetic Data")
    
    # Validate real data
    if REAL_DATA:
        real_report = validate_dataset(REAL_DATA, "Real Data")
        clean_real = real_report['valid']
    else:
        print("\n⚠️  No real data yet — using synthetic only")
        clean_real = []
    
    # Merge
    combined = synthetic_report['valid'] + clean_real
    
    # Final validation
    final_report = validate_dataset(combined, "COMBINED DATASET")
    
    print(f"\n{'='*50}")
    print(f"FINAL DATASET READY")
    print(f"Total: {final_report['total_valid']} examples")
    print(f"Bugs: {final_report['bug_count']}")
    print(f"Failed TC: {final_report['failed_tc_count']}")
    print(f"{'='*50}")
    
    return final_report['valid']

if __name__ == "__main__":
    data = merge_and_prepare()
    print(f"\nReady to train on {len(data)} examples")