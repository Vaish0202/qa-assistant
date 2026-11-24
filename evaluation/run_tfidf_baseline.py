# evaluation/run_tfidf_baseline.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
import numpy as np
from sample_data.test_cases import TEST_CASES

# Prepare data
X = []
y = []
for tc in TEST_CASES:
    # Combine all text fields
    text = f"{tc['testcase_logs']} {tc['testcase_description']} {tc['testcase_code']}"
    X.append(text)
    y.append(1 if tc['expected'] == 'bug' else 0)

# TF-IDF + Logistic Regression pipeline
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(max_features=500, ngram_range=(1,2))),
    ('clf', LogisticRegression(max_iter=1000, random_state=42))
])

# Cross validation
cv_scores = cross_val_score(pipeline, X, y, cv=5, scoring='accuracy')
print(f"TF-IDF + LR CV Accuracy: {cv_scores.mean():.1%} (+/- {cv_scores.std():.1%})")

# Train on all data and predict
pipeline.fit(X, y)
predictions = pipeline.predict(X)
correct = sum(1 for p, tc in zip(predictions, TEST_CASES)
              if (p==1) == (tc['expected']=='bug'))
print(f"TF-IDF + LR Accuracy: {correct}/{len(TEST_CASES)} = {correct/len(TEST_CASES):.1%}")

# Majority baseline
majority = max(sum(y), len(y)-sum(y)) / len(y)
print(f"Majority baseline: {majority:.1%}")