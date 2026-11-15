"""
Pipeline2 - Application Factory
Assembles Flask application, controllers, middleware, and route blueprints.
"""

from flask import Flask
from .config import FRONTEND_DIR
from .middleware import register_middleware
from .error_handlers import register_error_handlers
from backend.controllers.static_controller import serve_index, serve_assets
from backend.controllers.health_controller import check_system_health

from backend.routes.predict_routes import predict_bp
from backend.routes.simulator_routes import simulator_bp
from backend.routes.analytics_routes import analytics_bp


def create_app() -> Flask:
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")

    # Register cross-cutting concerns
    register_middleware(app)
    register_error_handlers(app)

    # Register route blueprints
    app.register_blueprint(predict_bp)
    app.register_blueprint(simulator_bp)
    app.register_blueprint(analytics_bp)

    # Core web & health routes
    app.add_url_rule("/", view_func=serve_index, methods=["GET"])
    app.add_url_rule("/<path:path>", view_func=serve_assets, methods=["GET"])
    app.add_url_rule("/api/health", view_func=check_system_health, methods=["GET"])

    return app
