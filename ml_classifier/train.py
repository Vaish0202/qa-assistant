import numpy as np
import pickle
from xgboost import XGBClassifier
from sklearn.model_selection import cross_val_score
from sklearn.metrics import classification_report
from ml_classifier.feature_extractor import extract_features
from ml_classifier.merge_data import merge_and_prepare

MODEL_PATH = "ml_classifier/qa_classifier_model.pkl"

def train_model():
    print("=" * 50)
    print("TRAINING QA CLASSIFIER — HYBRID ML + LLM")
    print("=" * 50)

    # Get merged + validated data
    training_data = merge_and_prepare()

    # Prepare features
    X, y = [], []
    for item in training_data:
        features = extract_features(
            item['logs'],
            item['description'],
            item['code']
        )
        X.append(features)
        y.append(1 if item['label'] == 'bug' else 0)

    X = np.array(X)
    y = np.array(y)

    print(f"\nFeature matrix shape: {X.shape}")

    # Train XGBoost
    model = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        eval_metric='logloss',
        random_state=42
    )

    # 5-fold cross validation
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
    print(f"\nCross-validation results:")
    print(f"  Each fold: {[f'{s:.2%}' for s in cv_scores]}")
    print(f"  Mean: {cv_scores.mean():.2%}")
    print(f"  Std: {cv_scores.std():.2%}")

    # Train final model on all data
    model.fit(X, y)

    # Save
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    print(f"\n✓ Model saved: {MODEL_PATH}")

    # Top features
    from ml_classifier.feature_extractor import get_feature_names
    feature_names = get_feature_names()
    importances = model.feature_importances_
    top = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)[:10]
    
    print("\nTop 10 predictive features:")
    for name, imp in top:
        bar = '█' * int(imp * 100)
        print(f"  {name:<35} {imp:.4f} {bar}")

    return model

if __name__ == "__main__":
    train_model()