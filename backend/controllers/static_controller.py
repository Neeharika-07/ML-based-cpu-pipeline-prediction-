"""
Pipeline2 - Static & UI File Controller
Serves the single-page application dashboard and client assets.
"""

import os
from flask import send_from_directory, jsonify
from backend.app.config import FRONTEND_DIR


def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return send_from_directory(FRONTEND_DIR, "index.html")
    return jsonify({
        "name": "Pipeline2 API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": [
            "/api/health",
            "/api/predict",
            "/api/predict/batch",
            "/api/simulate/run",
            "/api/simulate/compare",
            "/api/analytics/metrics",
            "/api/analytics/metadata",
            "/api/analytics/traces"
        ]
    })


def serve_assets(path):
    if path.startswith("api/"):
        return jsonify({"status": "error", "message": f"API endpoint not found: /{path}"}), 404
    target_path = os.path.join(FRONTEND_DIR, path)
    if os.path.exists(target_path):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")
