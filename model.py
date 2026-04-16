"""
ML Model Module — AI Financial Intelligence Engine

Isolation Forest for anomaly detection in spending patterns.
"""

import os
import time
import logging
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib

logger = logging.getLogger("ai_finance.model")

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "spending_model.pkl")

EXPECTED_FEATURES = 9

FEATURE_NAMES = [
    "login_deviation",
    "amount_deviation",
    "device_flag",
    "location_flag",
    "attempts",
    "transaction_velocity",
    "time_since_last_transaction",
    "daily_usage_ratio",
    "transaction_frequency",
]

_model = None

# ─── DATA GENERATION ─────────────────────────────────────────────────────────────

def generate_training_data(n_samples=2000):
    rng = np.random.RandomState(42)

    login_deviation = rng.exponential(1.0, n_samples).clip(0, 12)
    amount_deviation = rng.exponential(0.15, n_samples).clip(0, 5)
    device_flag = rng.choice([0, 1], n_samples, p=[0.92, 0.08])
    location_flag = rng.choice([0, 1], n_samples, p=[0.90, 0.10])
    attempts = rng.choice([1, 2, 3], n_samples)
    velocity = rng.poisson(1.0, n_samples).clip(0, 10)
    time_since_last = rng.exponential(120, n_samples).clip(5, 1440)
    daily_usage_ratio = rng.beta(2, 8, n_samples).clip(0, 1)
    frequency = rng.exponential(2.0, n_samples).clip(0.1, 20)

    data = np.column_stack([
        login_deviation,
        amount_deviation,
        device_flag,
        location_flag,
        attempts,
        velocity,
        time_since_last,
        daily_usage_ratio,
        frequency,
    ])

    # Inject anomalies (5%)
    n_anomalies = int(n_samples * 0.05)
    idx = rng.choice(n_samples, n_anomalies, replace=False)

    for i in idx:
        data[i] = [
            rng.uniform(6, 12),
            rng.uniform(2, 10),
            1, 1,
            rng.randint(3, 8),
            rng.randint(5, 15),
            rng.uniform(0, 5),
            rng.uniform(0.8, 1.5),
            rng.uniform(15, 50),
        ]

    return data

# ─── VALIDATION ─────────────────────────────────────────────────────────────────

def validate_features(features):
    features = np.array(features).reshape(1, -1)

    if features.shape[1] != EXPECTED_FEATURES:
        raise ValueError(f"Invalid feature size: expected {EXPECTED_FEATURES}, got {features.shape[1]}")

    return features.astype(float)

# ─── EVALUATION ───────────────────────────────────────────────────────────

def evaluate_model(model, data):
    n_samples = data.shape[0]
    n_anomalies = int(n_samples * 0.05)

    # Ground truth (last 5% anomalies)
    y_true = np.ones(n_samples)
    y_true[-n_anomalies:] = -1

    y_pred = model.predict(data)
    accuracy = np.mean(y_true == y_pred)

    return {
        "accuracy": round(float(accuracy), 4),
        "total_samples": n_samples,
        "actual_anomalies": n_anomalies,
        "detected_anomalies": int(np.sum(y_pred == -1)),
    }

# ─── TRAIN MODEL ────────────────────────────────────────────────────────────────

def train_model():
    global _model

    logger.info("Training Isolation Forest model...")

    data = generate_training_data()

    model = IsolationForest(
        n_estimators=100,
        contamination=0.05,
        random_state=42
    )

    model.fit(data)

    # Evaluate model
    evaluation = evaluate_model(model, data)

    print(f"Model Accuracy: {evaluation['accuracy'] * 100}%")
    print(f"Detected Anomalies: {evaluation['detected_anomalies']}")

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    _model = model
    return model

# ─── LOAD MODEL ────────────────────────────────────────────────────────────────

def load_model():
    global _model

    if not os.path.exists(MODEL_PATH):
        return train_model()

    _model = joblib.load(MODEL_PATH)
    logger.info(f"Model loaded from {MODEL_PATH}")
    return _model

def get_model():
    global _model
    if _model is None:
        _model = load_model()
    return _model

# ─── PREDICT ───────────────────────────────────────────────────────────────────

def predict(features):
    model = get_model()
    try:
        features = validate_features(features)
        pred = model.predict(features)[0]
        score = model.decision_function(features)[0]

        # Convert to risk score [0, 100]
        risk_score = max(0, min(100, 50 - score * 200))

        return {
            "prediction": "Suspicious" if pred == -1 else "Normal",
            "risk_score": round(float(risk_score), 2),
            "raw_score": round(float(score), 4),
        }
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return {
            "prediction": "Suspicious",
            "risk_score": 100.0,
            "error": str(e)
        }

# ─── MODEL INFO ──────────────────────────────────────────────────────────────────

def get_model_info():
    """Restored for app.py compatibility"""
    model = get_model()
    return {
        "model_type": "IsolationForest",
        "model_loaded": model is not None,
        "model_path": MODEL_PATH,
        "n_features_expected": EXPECTED_FEATURES,
        "feature_names": FEATURE_NAMES,
    }

if __name__ == "__main__":
    train_model()