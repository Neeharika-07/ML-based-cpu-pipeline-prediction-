"""
Pipeline2 - System Health Controller
Reports operational status of models, dataset, and CPU pipeline simulator.
"""

import os
from flask import jsonify
from backend.app.config import MODEL_DIR, DATASET_PATH


def check_system_health():
    xgb_path = os.path.join(MODEL_DIR, "branch_predictor_xgb.joblib")
    return jsonify({
        "status": "healthy",
        "server": "Pipeline2 Backend",
        "models_ready": os.path.exists(xgb_path),
        "dataset_ready": os.path.exists(DATASET_PATH),
        "architecture": "5-Stage RISC Pipeline (IF, ID, EX, MEM, WB)"
    })
