#!/usr/bin/env python3
"""Mock backend server for testing CodeBook.

This Flask server simulates a backend service that resolves template expressions.
It provides configurable values that can be changed at runtime for testing.

Usage:
    python mock_server.py [--port PORT]

The server runs on http://localhost:3000 by default.
"""

# Suppress Python 3.13+ free-threaded GIL warning from watchdog (used by Flask debug mode)
import warnings

warnings.filterwarnings("ignore", message=".*GIL.*")

import argparse

from flask import Flask, jsonify, request

app = Flask(__name__)

# Simulated data store - can be modified via API
# All templates must start with "server." prefix
DATA = {
    "server.SCIP.language_count": 13,
    "server.metrics.files_indexed": 1000,
    "server.metrics.concurrent_workers": 5,
    "server.project.version": "1.2.3",
    "server.project.name": "CICADA",
    "server.project.file_count": 42,
    "server.project.primary_language": "Python",
    "server.stats.total_users": 42,
    "server.stats.active_sessions": 7,
    "server.config.max_connections": 100,
    "server.config.timeout_ms": 5000,
    "server.API.endpoint_count": 127,
    "server.API.get_response_time": "145ms",
    "server.CI.build_status": "Passing",
}


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})


@app.route("/resolve/<path:template>")
def resolve(template: str):
    """Resolve a single template expression.

    Args:
        template: The template expression (e.g., "SCIP.language_count")

    Returns:
        JSON with resolved value or 404 if not found
    """
    if template in DATA:
        return jsonify({"value": DATA[template]})
    return jsonify({"error": f"Unknown template: {template}"}), 404


@app.route("/resolve/batch", methods=["POST"])
def resolve_batch():
    """Resolve multiple template expressions at once.

    Request body:
        {"templates": ["template1", "template2", ...]}

    Returns:
        JSON with resolved values for known templates
    """
    body = request.get_json()
    templates = body.get("templates", [])

    values = {}
    for template in templates:
        if template in DATA:
            values[template] = DATA[template]

    return jsonify({"values": values})


@app.route("/data", methods=["GET"])
def get_data():
    """Get all available data (for debugging)."""
    return jsonify(DATA)


@app.route("/data/<path:template>", methods=["PUT"])
def set_data(template: str):
    """Update a data value (for testing dynamic updates).

    Args:
        template: The template key to update

    Request body:
        {"value": new_value}
    """
    body = request.get_json()
    DATA[template] = body.get("value")
    return jsonify({"updated": template, "value": DATA[template]})


@app.route("/data/<path:template>", methods=["DELETE"])
def delete_data(template: str):
    """Delete a data value."""
    if template in DATA:
        del DATA[template]
        return jsonify({"deleted": template})
    return jsonify({"error": f"Unknown template: {template}"}), 404


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mock CodeBook backend server")
    parser.add_argument("--port", "-p", type=int, default=3000, help="Port to run the server on")
    args = parser.parse_args()

    print("Starting mock CodeBook backend server...")
    print("Available templates:", list(DATA.keys()))
    print("\nEndpoints:")
    print("  GET  /health             - Health check")
    print("  GET  /resolve/<template> - Resolve single template")
    print("  POST /resolve/batch      - Resolve multiple templates")
    print("  GET  /data               - List all data")
    print("  PUT  /data/<template>    - Update a value")
    print("  DELETE /data/<template>  - Delete a value")
    print(f"\nServer running on http://localhost:{args.port}")
    app.run(host="localhost", port=args.port, debug=True)
