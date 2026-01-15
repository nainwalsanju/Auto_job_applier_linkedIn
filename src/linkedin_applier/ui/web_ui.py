"""
Web UI Module for LinkedIn Auto Job Applier

This module provides a simple web interface for the application.

Usage:
    from src.linkedin_applier.ui.web_ui import create_app

    app = create_app()
    app.run(host='0.0.0.0', port=5000)
"""

from flask import Flask, render_template, request, jsonify
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def create_app(template_folder: str = None) -> Flask:
    """
    Create Flask application.

    Args:
        template_folder: Path to templates directory

    Returns:
        Flask application instance
    """
    app = Flask(__name__, template_folder=template_folder or str(PROJECT_ROOT / "templates"))

    @app.route("/")
    def index():
        """Render main page."""
        return render_template("index.html")

    @app.route("/api/status")
    def status():
        """Return application status."""
        return jsonify(
            {
                "status": "ready",
                "version": "1.0.0",
                "modules": ["jobs", "forms", "ai", "core", "utils", "exceptions"],
            }
        )

    @app.route("/api/config")
    def config():
        """Return configuration info."""
        from src.linkedin_applier.config import load_legacy_config

        config = load_legacy_config()
        return jsonify(config)

    return app


def run_ui(host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
    """
    Run the web UI.

    Args:
        host: Host to bind to
        port: Port to listen on
        debug: Enable debug mode
    """
    app = create_app()
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    print("Starting web UI...")
    run_ui(host="0.0.0.0", port=5000, debug=True)
