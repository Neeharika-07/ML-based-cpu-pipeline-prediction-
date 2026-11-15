"""
PipelineAI - Machine Learning Training & Evaluation Module
Trains and benchmarks multiple branch predictors:
  1. Static Baseline (Always Taken / Not Taken)
  2. 2-Bit Saturating Counter (Bimodal Smith Predictor)
  3. Gshare Hardware Branch Predictor
  4. Perceptron Neural Predictor (Jiménez & Lin)
  5. Random Forest Classifier
  6. XGBoost / Gradient Boosting Classifier (Production AI Model)

Saves the best model artifact, feature importance, and benchmark metrics to ml/model/.
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix
)
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml.preprocessing import BranchPreprocessor, DEFAULT_HIST_LEN, DEFAULT_PC_MOD
from ml.baseline_models import (
    TwoBitSaturatingCounterPredictor,
    GsharePredictor,
    PerceptronPredictor
)


def evaluate_model(model, X_test: pd.DataFrame, y_test: pd.Series, name: str) -> Dict[str, Any]:
    """Calculates comprehensive microarchitectural and ML evaluation metrics."""
    start_t = time.perf_counter()
    preds = model.predict(X_test)
    inference_time = (time.perf_counter() - start_t) * 1000.0  # ms

    acc = float(accuracy_score(y_test, preds))
    misprediction_rate = float(1.0 - acc)
    mpki = float(misprediction_rate * 200.0)

    try:
        proba = model.predict_proba(X_test)[:, 1]
        auc = float(roc_auc_score(y_test, proba))
    except Exception:
        auc = float(acc)

    cm = confusion_matrix(y_test, preds).tolist()

    metrics = {
        "model_name": name,
        "accuracy": round(acc, 4),
        "misprediction_rate": round(misprediction_rate, 4),
        "mpki": round(mpki, 2),
        "precision": round(float(precision_score(y_test, preds, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, preds, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, preds, zero_division=0)), 4),
        "roc_auc": round(auc, 4),
        "inference_latency_ms": round(inference_time, 2),
        "samples_evaluated": len(y_test),
        "confusion_matrix": cm
    }
    return metrics


def train_pipeline(
    data_path: str = "dataset/processed_dataset.csv",
    model_dir: str = "ml/model",
    quick_mode: bool = False
):
    os.makedirs(model_dir, exist_ok=True)
    print(f"[Train] Loading dataset from {data_path}...")
    X_train, y_train, X_val, y_val, X_test, y_test = BranchPreprocessor.load_splits(data_path)
    print(f"[Train] Train samples: {len(X_train):,}, Val samples: {len(X_val):,}, Test samples: {len(X_test):,}")

    if quick_mode:
        print("[Train] Running in quick mode (subsampling for rapid verification)...")
        X_train = X_train.iloc[:30000]
        y_train = y_train.iloc[:30000]

    all_metrics = {}

    # 1. Bimodal 2-Bit Saturating Counter
    print("[Train] Training 2-Bit Saturating Counter Predictor...")
    bimodal = TwoBitSaturatingCounterPredictor()
    bimodal.fit(X_train, y_train)
    all_metrics["Bimodal_2Bit"] = evaluate_model(bimodal, X_test, y_test, "Bimodal (2-Bit Counter)")

    # 2. Gshare Predictor
    print("[Train] Training Gshare Hardware Predictor...")
    gshare = GsharePredictor()
    gshare.fit(X_train, y_train)
    all_metrics["Gshare"] = evaluate_model(gshare, X_test, y_test, "Gshare (Hardware XOR)")

    # 3. Perceptron Neural Predictor
    print("[Train] Training Jiménez-Lin Perceptron Predictor...")
    perceptron = PerceptronPredictor()
    perceptron.fit(X_train, y_train)
    all_metrics["Perceptron"] = evaluate_model(perceptron, X_test, y_test, "Perceptron (Neural)")

    # 4. Random Forest Classifier
    print("[Train] Training Random Forest Classifier...")
    rf = RandomForestClassifier(n_estimators=40, max_depth=12, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    all_metrics["RandomForest"] = evaluate_model(rf, X_test, y_test, "Random Forest")

    # 5. XGBoost Classifier (Flagship AI Model)
    print("[Train] Training XGBoost Classifier...")
    xgb_model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1
    )
    xgb_model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )
    all_metrics["XGBoost"] = evaluate_model(xgb_model, X_test, y_test, "XGBoost (PipelineAI Engine)")

    # Feature Importance from XGBoost
    feature_names = list(X_train.columns)
    importances = xgb_model.feature_importances_.tolist()
    feature_importance = [
        {"feature": name, "importance": round(float(imp), 4)}
        for name, imp in sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)
    ]

    # Save models
    xgb_path = os.path.join(model_dir, "branch_predictor_xgb.joblib")
    joblib.dump(xgb_model, xgb_path)
    print(f"[Train] Saved flagship model to {xgb_path}")

    baselines_path = os.path.join(model_dir, "baseline_predictors.joblib")
    joblib.dump({
        "bimodal": bimodal,
        "gshare": gshare,
        "perceptron": perceptron,
        "random_forest": rf
    }, baselines_path)
    print(f"[Train] Saved baseline models to {baselines_path}")

    # Save metrics and feature metadata
    metrics_path = os.path.join(model_dir, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(all_metrics, f, indent=2)
    print(f"[Train] Saved metrics to {metrics_path}")

    meta_path = os.path.join(model_dir, "model_meta.json")
    meta_info = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "features": feature_names,
        "feature_importance": feature_importance,
        "best_model": "XGBoost",
        "dataset_samples": {
            "train": len(X_train),
            "val": len(X_val),
            "test": len(X_test)
        }
    }
    with open(meta_path, "w") as f:
        json.dump(meta_info, f, indent=2)
    print(f"[Train] Saved metadata to {meta_path}")

    print("\n" + "="*70)
    print("BRANCH PREDICTION BENCHMARK SUMMARY (TEST SET - 30,000 SAMPLES)")
    print("="*70)
    print(f"{'Model':<24} | {'Accuracy':<10} | {'Mispred %':<10} | {'MPKI':<8} | {'F1 Score':<8}")
    print("-" * 70)
    for key, m in all_metrics.items():
        print(f"{m['model_name']:<24} | {m['accuracy']*100:.2f}%     | {m['misprediction_rate']*100:.2f}%     | {m['mpki']:<8.2f} | {m['f1']:<8.4f}")
    print("="*70)


def main():
    parser = argparse.ArgumentParser(description="PipelineAI Training Script")
    parser.add_argument("--data", default="dataset/processed_dataset.csv", help="Path to processed dataset")
    parser.add_argument("--output-dir", default="ml/model", help="Directory to save models")
    parser.add_argument("--quick", action="store_true", help="Quick mode with subsampled training")
    args = parser.parse_args()

    train_pipeline(data_path=args.data, model_dir=args.output_dir, quick_mode=args.quick)


if __name__ == "__main__":
    main()
