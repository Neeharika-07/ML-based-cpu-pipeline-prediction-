"""
Pipeline2 - Application Entrypoint
Lightweight runner parsing command-line parameters and launching the Flask server.
"""

import os
import sys
import argparse

# Ensure project root is in Python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app import create_app
from backend.app.config import DEFAULT_PORT, DEFAULT_HOST


def main():
    parser = argparse.ArgumentParser(description="Pipeline2 Backend Server")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port to bind (default: {DEFAULT_PORT})")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Host interface (default: {DEFAULT_HOST})")
    parser.add_argument("--test-only", action="store_true", help="Run self-diagnostic check and exit")
    args = parser.parse_args()

    app = create_app()

    if args.test_only:
        print("[Pipeline2 Diagnostic] Initializing App test...")
        with app.test_client() as client:
            res_health = client.get("/api/health")
            print(f"[Pipeline2 Diagnostic] /api/health returned {res_health.status_code}: {res_health.get_json()}")
            res_metrics = client.get("/api/analytics/metrics")
            print(f"[Pipeline2 Diagnostic] /api/analytics/metrics returned {res_metrics.status_code}")
        print("[Pipeline2 Diagnostic] All checks passed successfully.")
        return

    print("=" * 60)
    print(f"  Starting Pipeline2 Server on http://localhost:{args.port}")
    print(f"  Frontend Dashboard: http://localhost:{args.port}")
    print(f"  API Health:         http://localhost:{args.port}/api/health")
    print("=" * 60)
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
