"""
PipelineAI - Simulator Routes
Endpoints for running cycle-accurate 5-stage CPU pipeline simulations.
"""

import os
from flask import request, jsonify
import pandas as pd
from . import simulator_bp
from backend.simulator import CPUPipelineSimulator

sim = CPUPipelineSimulator()

DATASET_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "dataset",
    "raw_dataset.csv"
)

# Cache loaded traces in memory for rapid simulation
_CACHED_TRACES = {}


def _get_trace_data(trace_id: int = 0, limit: int = 150):
    global _CACHED_TRACES
    if trace_id not in _CACHED_TRACES:
        if os.path.exists(DATASET_PATH):
            df = pd.read_csv(DATASET_PATH)
            # Drop warmup rows with missing PC
            df = df.dropna(subset=["pc"])
            # Filter by trace_num
            trace_df = df[df["trace_num"] == trace_id].sort_values("branch_index").reset_index(drop=True)
            _CACHED_TRACES[trace_id] = trace_df
        else:
            return []

    df = _CACHED_TRACES.get(trace_id, pd.DataFrame())
    subset = df.head(limit).to_dict(orient="records")
    return subset


@simulator_bp.route("/run", methods=["POST"])
def run_simulation():
    """
    Executes a CPU pipeline simulation on a trace segment.
    Payload:
      {
        "trace_id": 0,
        "predictor": "xgboost" | "perceptron" | "gshare" | "bimodal" | "static_not_taken",
        "sample_limit": 100,
        "penalty": 2
      }
    """
    data = request.get_json(force=True, silent=True) or {}
    trace_id = int(data.get("trace_id", 0))
    predictor = data.get("predictor", "xgboost")
    sample_limit = min(int(data.get("sample_limit", 100)), 1000)
    penalty = int(data.get("penalty", 2))

    sim.misprediction_penalty = penalty

    # Check if custom branches were provided or use trace dataset
    branches = data.get("custom_branches")
    if not branches:
        branches = _get_trace_data(trace_id=trace_id, limit=sample_limit)

    if not branches:
        return jsonify({
            "status": "error",
            "message": f"No branch records found for trace_id={trace_id}"
        }), 404

    results = sim.run_trace(branches, predictor_type=predictor, record_cycles=True)

    return jsonify({
        "status": "success",
        "trace_id": trace_id,
        "sample_count": len(branches),
        "results": results
    })


@simulator_bp.route("/compare", methods=["POST"])
def compare_architectures():
    """
    Runs trace comparison across all predictor types.
    Payload:
      {
        "trace_id": 0,
        "sample_limit": 200
      }
    """
    data = request.get_json(force=True, silent=True) or {}
    trace_id = int(data.get("trace_id", 0))
    sample_limit = min(int(data.get("sample_limit", 200)), 1000)

    branches = _get_trace_data(trace_id=trace_id, limit=sample_limit)
    if not branches:
        return jsonify({
            "status": "error",
            "message": f"No branch records found for trace_id={trace_id}"
        }), 404

    comparison = sim.compare_all_predictors(branches, max_samples=sample_limit)

    return jsonify({
        "status": "success",
        "trace_id": trace_id,
        "branches_tested": len(branches),
        "comparison": comparison
    })
