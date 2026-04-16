"""
Model Training Script
Run this to train and save the Isolation Forest model before starting the API.

Produces:
    models/spending_model.pkl    — Trained Isolation Forest model
    models/model_metadata.pkl    — Training metadata (feature names, stats, etc.)

Usage:
    python train_model.py
"""

import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-28s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("ai_finance.train")


def main():
    logger.info("=" * 60)
    logger.info("  AI FINANCIAL INTELLIGENCE — Model Training")
    logger.info("=" * 60)

    from model import (
        train_model,
        generate_training_data,
        get_model_info,
        validate_features,
        MODEL_PATH,
        FEATURE_NAMES,
        EXPECTED_FEATURES,
    )
    import numpy as np

    # ── Dataset Info ──────────────────────────────────────────────────────────
    data = generate_training_data()
    logger.info(f"Training data shape: {data.shape}")
    logger.info(f"Feature count: {EXPECTED_FEATURES}")
    logger.info(f"Feature names: {', '.join(FEATURE_NAMES)}")
    logger.info(f"Sample means: {np.mean(data, axis=0).round(3)}")
    logger.info(f"Sample stds:  {np.std(data, axis=0).round(3)}")

    # ── Train and Save ────────────────────────────────────────────────────────
    model = train_model(save=True)

    # ── Feature Validation Test ───────────────────────────────────────────────
    logger.info("-" * 60)
    logger.info("Feature Validation Tests:")

    # Test correct shape
    good_input = np.array([[1.0, 0.1, 0, 0, 1, 1, 120.0, 0.15, 2.5]])
    validated = validate_features(good_input)
    logger.info(f"  ✅ Valid 9-feature input: shape={validated.shape}")

    # Test 1D input auto-reshape
    flat_input = np.array([1.0, 0.1, 0, 0, 1, 1, 120.0, 0.15, 2.5])
    validated = validate_features(flat_input)
    logger.info(f"  ✅ 1D auto-reshape: shape={validated.shape}")

    # Test NaN handling
    nan_input = np.array([[1.0, np.nan, 0, 0, 1, 1, 120.0, 0.15, 2.5]])
    validated = validate_features(nan_input)
    logger.info(f"  ✅ NaN replaced: col[1] = {validated[0, 1]}")

    # Test wrong feature count
    try:
        bad_input = np.array([[1.0, 0.1, 0, 0, 1]])
        validate_features(bad_input)
        logger.error("  ❌ Should have raised ValueError for wrong feature count")
    except ValueError as e:
        logger.info(f"  ✅ Wrong feature count caught: {e}")

    # ── Model Prediction Validation ───────────────────────────────────────────
    logger.info("-" * 60)
    logger.info("Prediction Validation:")

    #                  login  amt   dev  loc  att  vel  time  daily  freq
    normal_sample  = np.array([[1.0,  0.1,  0,   0,   1,   1,   120.0, 0.15, 2.5]])
    anomaly_sample = np.array([[10.0, 5.0,  1,   1,   5,   8,   1.0,   0.95, 40.0]])

    normal_pred = model.predict(normal_sample)[0]
    anomaly_pred = model.predict(anomaly_sample)[0]
    normal_score = model.decision_function(normal_sample)[0]
    anomaly_score = model.decision_function(anomaly_sample)[0]

    normal_risk = max(0, min(100, (1 - normal_score) * 100))
    anomaly_risk = max(0, min(100, (1 - anomaly_score) * 100))

    logger.info(f"  Normal sample  → pred={normal_pred:+d}  score={normal_score:.4f}  risk={normal_risk:.1f}")
    logger.info(f"  Anomaly sample → pred={anomaly_pred:+d}  score={anomaly_score:.4f}  risk={anomaly_risk:.1f}")

    if normal_pred == 1 and anomaly_pred == -1:
        logger.info("  ✅ Classification validation PASSED")
    else:
        logger.warning("  ⚠️ Classification produced unexpected results")

    if anomaly_risk > normal_risk:
        logger.info("  ✅ Risk ordering validation PASSED (anomaly > normal)")
    else:
        logger.warning("  ⚠️ Risk ordering unexpected")

    # ── Model Info ────────────────────────────────────────────────────────────
    logger.info("-" * 60)
    info = get_model_info()
    logger.info("Model Info:")
    logger.info(f"  Model type:        {info.get('model_type')}")
    logger.info(f"  Features expected: {info.get('n_features_expected')}")
    logger.info(f"  Features actual:   {info.get('n_features_actual')}")
    logger.info(f"  Consistent:        {info.get('feature_consistent')}")
    logger.info(f"  Training samples:  {info.get('training_samples')}")
    logger.info(f"  Training time:     {info.get('training_duration_sec')}s")
    logger.info(f"  Model path:        {MODEL_PATH}")

    logger.info("=" * 60)
    logger.info("  TRAINING COMPLETE — Model ready for deployment")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
