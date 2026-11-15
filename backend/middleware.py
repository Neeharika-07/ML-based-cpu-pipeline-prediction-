"""
Pipeline2 - Middleware & Security Headers
Handles CORS headers and anti-caching directives for real-time dashboard updates.
"""

def register_middleware(app):
    @app.after_request
    def apply_response_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
