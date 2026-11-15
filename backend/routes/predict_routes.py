"""
PipelineAI - Prediction Routes
Handles real-time and batch branch prediction inference.
"""

from flask import request, jsonify
from . import predict_bp
from backend.simulator import CPUPipelineSimulator

# Instantiate shared simulator engine
simulator_engine = CPUPipelineSimulator()


@predict_bp.route("", methods=["POST"])
def predict_single_branch():
    """
    Predicts outcome for a single branch instruction.
    Payload:
      {
        "pc": "0x401020" or 4198432,
        "history": "1101001011000101" or [1, 1, 0, ...],
        "predictor": "xgboost" | "perceptron" | "gshare" | "bimodal"
      }
    """
    data = request.get_json(force=True, silent=True) or {}
    pc = data.get("pc", 0)
    history = data.get("history", [0] * 16)
    predictor = data.get("predictor", "xgboost")

    # Set simulator BHR temporarily
    if isinstance(history, str):
        bhr = [int(b) for b in history.replace(" ", "") if b in "01"][:16]
        while len(bhr) < 16:
            bhr.insert(0, 0)
    elif isinstance(history, list):
        bhr = [int(x) for x in history][:16]
        while len(bhr) < 16:
            bhr.insert(0, 0)
    else:
        bhr = [0] * 16

    simulator_engine.bhr = bhr
    if isinstance(pc, str):
        pc_int = int(pc, 16) if pc.startswith("0x") or pc.startswith("0X") else int(pc)
    else:
        pc_int = int(pc)

    pred, confidence = simulator_engine.predict_branch(pc_int, predictor)

    return jsonify({
        "status": "success",
        "pc": pc_int,
        "pc_hex": hex(pc_int),
        "pc_idx": pc_int % 4096,
        "history": bhr,
        "history_str": "".join(map(str, bhr)),
        "predictor": predictor,
        "prediction": pred,
        "prediction_label": "TAKEN" if pred == 1 else "NOT_TAKEN",
        "confidence": confidence
    })


@predict_bp.route("/batch", methods=["POST"])
def predict_batch():
    """
    Predicts outcomes for an array of branch instructions.
    Payload:
      {
        "branches": [{"pc": 12345, "history": "0101..."}, ...],
        "predictor": "xgboost"
      }
    """
    data = request.get_json(force=True, silent=True) or {}
    branches = data.get("branches", [])
    predictor = data.get("predictor", "xgboost")

    results = []
    for item in branches:
        pc = item.get("pc", 0)
        hist = item.get("history", [0] * 16)
        if isinstance(pc, str):
            pc_int = int(pc, 16) if pc.startswith("0x") or pc.startswith("0X") else int(pc)
        else:
            pc_int = int(pc)

        simulator_engine.bhr = [int(b) for b in (hist if isinstance(hist, list) else [0]*16)]
        pred, conf = simulator_engine.predict_branch(pc_int, predictor)
        results.append({
            "pc": pc_int,
            "prediction": pred,
            "prediction_label": "TAKEN" if pred == 1 else "NOT_TAKEN",
            "confidence": conf
        })

    return jsonify({
        "status": "success",
        "count": len(results),
        "results": results
    })
