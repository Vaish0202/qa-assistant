import numpy as np
import pickle
import os
from ml_classifier.feature_extractor import extract_features

MODEL_PATH = "ml_classifier/qa_classifier_model.pkl"

def load_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model not found at {MODEL_PATH}. Run train.py first."
        )
    with open(MODEL_PATH, 'rb') as f:
        return pickle.load(f)

# Load once at module level
_model = None

def get_model():
    global _model
    if _model is None:
        _model = load_model()
    return _model

def predict_classification(
    logs: str,
    description: str,
    code: str
) -> dict:
    """
    Fast ML-based classification
    Returns same format as old LLM classifier
    """
    model = get_model()
    features = extract_features(logs, description, code)
    features_2d = features.reshape(1, -1)

    # Predict
    prediction = model.predict(features_2d)[0]
    probabilities = model.predict_proba(features_2d)[0]

    classification = "bug" if prediction == 1 else "failed_testcase"
    confidence = float(probabilities[prediction])

    print(f"ML Classifier: {classification} (confidence: {confidence:.2%})")

    return {
        "classification": classification,
        "confidence": confidence,
        "method": "ml_xgboost",
        "bug_probability": float(probabilities[1]),
        "failed_tc_probability": float(probabilities[0])
    }