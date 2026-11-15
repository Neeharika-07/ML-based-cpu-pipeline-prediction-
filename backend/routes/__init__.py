"""
PipelineAI - Backend Routes Initialization
"""
from flask import Blueprint

predict_bp = Blueprint("predict", __name__, url_prefix="/api/predict")
simulator_bp = Blueprint("simulator", __name__, url_prefix="/api/simulate")
analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")

from . import predict_routes, simulator_routes, analytics_routes
