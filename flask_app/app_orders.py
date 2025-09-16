from flask import Blueprint, request, jsonify, send_file
from pathlib import Path
from datetime import datetime
from uuid import uuid4
import json

# Create a Flask Blueprint for order routes
orders_bp = Blueprint("orders", __name__)

# === Save location on your server ===
ORDERS_ROOT = Path(r"D:\Orders")
ORDERS_ROOT.mkdir(parents=True, exist_ok=True)  # make sure folder exists

def order_dir(order_id: str) -> Path:
    """Return (and create) the folder for a given order ID."""
    d = ORDERS_ROOT / order_id
    d.mkdir(parents=True, exist_ok=True)
    return d

@orders_bp.post("/api/orders")
def create_order():
    """Receive an order from the frontend, save JSON + placeholder PDF."""
    data = request.get_json(force=True)
    order_id = f"FLG-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid4())[:8]}"

    odir = order_dir(order_id)

    # Save the raw order data as JSON
    (odir / "order.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Save a placeholder PDF (swap for real PDF generator later)
    (odir / "quote.pdf").write_bytes(b"%PDF-1.4\n% Fake minimal PDF\n")

    return jsonify({
        "ok": True,
        "order_id": order_id,
        "files": {
            "json": str(odir / "order.json"),
            "pdf": str(odir / "quote.pdf")
        }
    }), 201

@orders_bp.get("/api/orders")
def list_orders():
    """List all saved orders."""
    items = []
    for d in ORDERS_ROOT.iterdir():
        if d.is_dir():
            json_path = d / "order.json"
            meta = {"order_id": d.name}
            if json_path.exists():
                try:
                    meta["data"] = json.loads(json_path.read_text(encoding="utf-8"))
                except Exception:
                    meta["data"] = None
            items.append(meta)
    return jsonify(sorted(items, key=lambda x: x["order_id"], reverse=True))

@orders_bp.get("/api/orders/<order_id>/pdf")
def get_order_pdf(order_id):
    """Serve the saved PDF back to the client."""
    path = order_dir(order_id) / "quote.pdf"
    if not path.exists():
        return {"error": "Not found"}, 404
    return send_file(path, mimetype="application/pdf")
