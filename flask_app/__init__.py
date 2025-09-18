+71
-0

"""Flask application for legacy Fastline endpoints.

This lightweight application keeps the historical routes that were
previously exposed by the Windows IIS site so that the main orders
service (``ghl_sync_orders_flask_service.py``) can focus on the new
workflow that runs on port 5050.  The routes here either provide a stub
implementation for backwards compatibility or proxy to the orders
service when appropriate.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from flask import Flask, current_app, jsonify, request

from .orders import orders_bp


ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    app.register_blueprint(orders_bp)

    @app.get("/healthz")
    def healthz() -> Dict[str, Any]:
        return {"ok": True}

    @app.post("/send-email")
    def send_email():
        payload = request.get_json(silent=True) or {}
        current_app.logger.info("send-email invoked", extra={"payload": payload})
        return jsonify({"ok": True, "message": "Email queued (stub)."}), 202

    @app.post("/sharepoint/upload")
    def upload_sharepoint():
        payload = request.get_json(silent=True) or {}
        current_app.logger.info("sharepoint/upload invoked", extra={"payload": payload})
        return (
            jsonify(
                {
                    "ok": True,
                    "message": "SharePoint upload queued (stub).",
                    "details": payload,
                }
            ),
            202,
        )

    @app.get("/")
    def index():
        return (
            "Fastline Flask app is running. Use /orders for the proxy to the"
            " orders service.",
            200,
            {"Content-Type": "text/plain; charset=utf-8"},
        )

    logging.basicConfig(level=logging.INFO)
    return app


app = create_app()
