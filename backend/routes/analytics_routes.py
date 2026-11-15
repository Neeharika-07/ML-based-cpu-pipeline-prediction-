"""
PipelineAI - Analytics & Metadata Routes
Provides model performance benchmarks, feature importance, and trace summaries.
"""

import os
import json
from flask import jsonify, request
import pandas as pd
from . import analytics_bp

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_DIR = os.path.join(BASE_DIR, "ml", "model")
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "raw_dataset.csv")


@analytics_bp.route("/metrics", methods=["GET"])
def get_model_metrics():
    """Returns benchmark metrics for all trained predictors."""
    metrics_file = os.path.join(MODEL_DIR, "metrics.json")
    if os.path.exists(metrics_file):
        with open(metrics_file, "r") as f:
            metrics = json.load(f)
        return jsonify({"status": "success", "metrics": metrics})
    else:
        return jsonify({
            "status": "error",
            "message": "Metrics not found. Please train models first using ml/train.py."
        }), 404


@analytics_bp.route("/metadata", methods=["GET"])
def get_metadata():
    """Returns model metadata and feature importance."""
    meta_file = os.path.join(MODEL_DIR, "model_meta.json")
    if os.path.exists(meta_file):
        with open(meta_file, "r") as f:
            meta = json.load(f)
        return jsonify({"status": "success", "metadata": meta})
    else:
        return jsonify({
            "status": "error",
            "message": "Metadata not found."
        }), 404


@analytics_bp.route("/traces", methods=["GET"])
def list_traces():
    """Lists available traces in the dataset and branch counts."""
    if not os.path.exists(DATASET_PATH):
        return jsonify({"status": "error", "message": "Dataset not found."}), 404

    try:
        df = pd.read_csv(DATASET_PATH)
        df = df.dropna(subset=["pc"])
        summary = []
        for trace_id, group in df.groupby("trace_num"):
            taken_cnt = int(group["taken"].sum())
            total = len(group)
            summary.append({
                "trace_id": int(trace_id),
                "total_branches": total,
                "taken_count": taken_cnt,
                "not_taken_count": total - taken_cnt,
                "taken_percentage": round((taken_cnt / total) * 100, 2)
            })
        return jsonify({"status": "success", "traces": summary})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route("/traces/<int:trace_id>", methods=["GET"])
def get_trace_branches(trace_id: int):
    """Returns branch sequence for a specific trace with pagination."""
    limit = min(int(request.args.get("limit", 50)), 500)
    offset = int(request.args.get("offset", 0))

    if not os.path.exists(DATASET_PATH):
        return jsonify({"status": "error", "message": "Dataset not found."}), 404

    try:
        df = pd.read_csv(DATASET_PATH)
        # Drop warmup branches with missing PC so calculations don't throw NaN errors
        df = df.dropna(subset=["pc"])
        trace_df = df[df["trace_num"] == trace_id].sort_values("branch_index").reset_index(drop=True)

        total = len(trace_df)
        page_df = trace_df.iloc[offset:offset+limit].copy()

        def safe_hex(val):
            try:
                return hex(int(float(val)))
            except Exception:
                return "0x0"

        def safe_idx(val):
            try:
                return int(float(val)) % 4096
            except Exception:
                return 0

        page_df["pc_hex"] = page_df["pc"].apply(safe_hex)
        page_df["pc_idx"] = page_df["pc"].apply(safe_idx)

        return jsonify({
            "status": "success",
            "trace_id": trace_id,
            "total_records": total,
            "offset": offset,
            "limit": limit,
            "branches": page_df.to_dict(orient="records")
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
