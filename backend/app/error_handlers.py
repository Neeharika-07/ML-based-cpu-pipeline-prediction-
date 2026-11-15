"""
Pipeline2 - Global Error Handlers
Provides JSON error responses for API endpoints and fallback routing for UI pages.
"""

import os
from flask import jsonify, request, send_from_directory
from .config import FRONTEND_DIR


def register_error_handlers(app):
    @app.errorhandler(404)
    def handle_404(e):
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "message": f"Endpoint not found: {request.path}"}), 404
        index_path = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_path):
            return send_from_directory(FRONTEND_DIR, "index.html")
        return jsonify({"status": "error", "message": "Resource not found"}), 404

    @app.errorhandler(500)
    def handle_500(e):
        return jsonify({"status": "error", "message": f"Internal server error: {str(e)}"}), 500
