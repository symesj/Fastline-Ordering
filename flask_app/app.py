from flask import Flask, request, jsonify
import base64, os
from werkzeug.utils import secure_filename
from datetime import datetime

from graph_mail import send_email_via_graph          # existing: email via Graph
from app_orders import orders_bp                      # existing: orders blueprint (saves to D:\Orders)
from graph_sharepoint import (                        # new: SharePoint upload helper
    upload_file_to_sharepoint, GraphError
)

app = Flask(__name__)

# --- Config ---
API_KEY = os.getenv("API_KEY", "super-secret-one-liner")
MAX_ATTACH_TOTAL_MB = 20  # Graph hard limit is 150MB, but keep safer

# --- Helpers ---
def _require_key(req):
    key = req.headers.get("x-api-key")
    return key == API_KEY

def _sum_bytes(attachments):
    return sum(len(a.get("contentBytes_b64", b"")) for a in attachments)

# --- Health check ---
@app.get("/health")
def health():
    return {"ok": True, "service": "flask_api"}, 200

# --- Email route ---
@app.route("/send-email", methods=["POST"])
def send_email():
    # ---- security
    if not _require_key(request):
        return jsonify({"error": "Forbidden"}), 403

    attachments = []
    payload_type = None

    # ---- OPTION A: JSON body (application/json) with base64 files
    if request.is_json:
        payload_type = "json"
        data = request.get_json(force=True)
        to_ = data.get("to")
        subject = data.get("subject")
        html_body = data.get("html_body", "")
        from_user = data.get("fromUser")

        # attachments: [{ filename, content_type, content_base64 }]
        for att in data.get("attachments", []):
            filename = secure_filename(att.get("filename", "file"))
            content_type = att.get("content_type", "application/octet-stream")
            content_b64 = att.get("content_base64")
            if not content_b64:
                continue
            attachments.append({
                "name": filename,
                "contentType": content_type,
                "contentBytes_b64": content_b64
            })

    # ---- OPTION B: multipart/form-data with file uploads
    else:
        payload_type = "multipart"
        to_ = request.form.get("to")
        subject = request.form.get("subject")
        html_body = request.form.get("html_body", "")
        from_user = request.form.get("fromUser")

        # files[] as multiple parts named "attachments"
        for file in request.files.getlist("attachments"):
            if not file or not file.filename:
                continue
            filename = secure_filename(file.filename)
            content = file.read()
            content_b64 = base64.b64encode(content).decode("utf-8")
            content_type = file.mimetype or "application/octet-stream"
            attachments.append({
                "name": filename,
                "contentType": content_type,
                "contentBytes_b64": content_b64
            })

    # ---- validation
    missing = [k for k in ["to_", "subject", "from_user"] if locals().get(k) in (None, "")]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # ---- size guard
    total_b64_bytes = _sum_bytes(attachments)
    total_mb = (total_b64_bytes * 3/4) / (1024*1024)  # approximate decoded size
    if total_mb > MAX_ATTACH_TOTAL_MB:
        return jsonify({"error": f"Attachments too large ({total_mb:.1f} MB). Limit {MAX_ATTACH_TOTAL_MB} MB."}), 413

    try:
        message_id = send_email_via_graph(
            to=to_,
            subject=subject,
            html_body=html_body,
            attachments=attachments,
            from_user=from_user
        )
        return jsonify({
            "status": "sent",
            "message_id": message_id,
            "attachments": [a["name"] for a in attachments],
            "mode": payload_type,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- NEW: SharePoint upload route ---
@app.post("/sharepoint/upload")
def sp_upload():
    # Security
    if not _require_key(request):
        return jsonify({"error": "Forbidden"}), 403

    # Accepts JSON: { "local_path": "D:\\Orders\\FLG-...\\quote.pdf",
    #                 "sp_folder":  "Shared Documents/Orders/FLG-..." }
    if not request.is_json:
        return jsonify({"error": "JSON required"}), 400

    data = request.get_json(force=True)
    local_path = data.get("local_path")
    sp_folder = data.get("sp_folder")

    if not local_path or not sp_folder:
        return jsonify({"error": "local_path and sp_folder are required"}), 400

    try:
        item_id, web_url = upload_file_to_sharepoint(local_path, sp_folder)
        return jsonify({"ok": True, "item_id": item_id, "webUrl": web_url}), 200
    except GraphError as ge:
        return jsonify({"error": str(ge)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Register other blueprints ---
app.register_blueprint(orders_bp)

# --- Entrypoint ---
if __name__ == "__main__":
    # 0.0.0.0 = reachable from LAN
    app.run(host="0.0.0.0", port=5000, debug=True)
