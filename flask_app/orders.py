from __future__ import annotations

import logging
import os
from typing import Any

import requests
from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

ORDERS_SERVICE_BASE = os.getenv("ORDERS_SERVICE_BASE", "http://127.0.0.1:5050")
ORDERS_API_KEY = os.getenv("X_API_KEY", os.getenv("ORDERS_API_KEY", ""))

orders_bp = Blueprint("orders", __name__, url_prefix="/orders")


def _service_url(path: str = "") -> str:
    base = ORDERS_SERVICE_BASE.rstrip("/")
    if path:
        return f"{base}/orders/{path.lstrip('/')}"
    return f"{base}/orders"


def _forward_response(resp: requests.Response):
    try:
        content: Any = resp.json()
    except ValueError:
        return (
            resp.text,
            resp.status_code,
            {"Content-Type": resp.headers.get("Content-Type", "text/plain; charset=utf-8")},
        )
    return jsonify(content), resp.status_code


@orders_bp.post("")
def proxy_create_order():
    payload = request.get_json(force=True)
    headers = {"Content-Type": "application/json"}
    if ORDERS_API_KEY:
        headers["x-api-key"] = ORDERS_API_KEY
    try:
        resp = requests.post(_service_url(), json=payload, headers=headers, timeout=30)
    except requests.RequestException as exc:
        logger.exception("Proxying order creation failed")
        return jsonify({"ok": False, "error": str(exc)}), 502
    return _forward_response(resp)


@orders_bp.get("/<path:extra>")
def proxy_passthrough(extra: str):
    headers = {}
    if ORDERS_API_KEY:
        headers["x-api-key"] = ORDERS_API_KEY
    try:
        resp = requests.get(_service_url(extra), headers=headers, timeout=30)
    except requests.RequestException as exc:
        logger.exception("Proxying GET to orders service failed")
        return jsonify({"ok": False, "error": str(exc)}), 502
    return _forward_response(resp)
