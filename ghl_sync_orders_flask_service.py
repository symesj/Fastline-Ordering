# GHL Sync & Orders – Flask Service
# ------------------------------------------------------------
# What this gives you
# - A production‑ready Flask service to:
#   1) Sync Contacts & Opportunities from GHL on a schedule
#   2) Receive GHL webhooks (e.g., order/payment events) and log/process them
#   3) Create internal Orders, generate a PDF, save to SharePoint, email the customer
# - Uses SQLAlchemy (SQLite by default) for durable logging
# - Ready for Windows service via NSSM
# ------------------------------------------------------------

"""
QUICK START
===========
1) Create a Python venv and install requirements.txt

   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt

2) Copy .env.example to .env and fill in your secrets.

3) Initialize the DB (SQLite by default):

   python app.py --init-db

4) Run locally

   python app.py
   # Service will start on http://127.0.0.1:5000 (or PORT from .env)

5) Set up Windows service (PowerShell, run as Admin) with NSSM

   $svc = "ghl_sync_service"
   nssm install $svc "C:\\Users\\fladmin\\Documents\\flask_app\\venv\\Scripts\\python.exe" \
       "C:\\Users\\fladmin\\Documents\\flask_app\\app.py"
   nssm set $svc AppDirectory "C:\\Users\\fladmin\\Documents\\flask_app"
   nssm set $svc AppEnvironmentExtra "FLASK_ENV=production"
   nssm start $svc

6) Point GHL webhooks to:

   https://<your-public-host>/webhooks/ghl

   (Use your IIS/NGINX reverse proxy or RDP+NGINX to expose port 5000 safely.)

7) Manual sync trigger:

   POST http://127.0.0.1:5000/sync/ghl  with header  x-api-key: <SYNC_API_KEY>

"""

# ------------------------
# requirements.txt
# ------------------------
# Flask==3.0.3
# python-dotenv==1.0.1
# requests==2.32.3
# SQLAlchemy==2.0.34
# apscheduler==3.10.4
# reportlab==4.2.2           # for PDF generation
# msal==1.30.0               # for Microsoft Graph auth (client credentials)
# tenacity==8.5.0            # robust retries


# ------------------------
# .env.example (copy to .env and fill in)
# ------------------------
# FLASK_ENV=production
# PORT=5000
# X_API_KEY=super-secret-one-liner
# SYNC_API_KEY=super-secret-one-liner
# DB_URL=sqlite:///ghl_sync.db
# LOG_LEVEL=INFO
#
# # GHL
# GHL_BASE_URL=https://rest.gohighlevel.com/v1
# GHL_API_KEY=REDACTED
# GHL_LOCATION_ID=REDACTED
#
# # Email + SharePoint via Microsoft Graph (app registration)
# MS_TENANT_ID=REDACTED
# MS_CLIENT_ID=REDACTED
# MS_CLIENT_SECRET=REDACTED
# MS_SENDER=sales@fastlinegroup.com
# SP_SITE_HOST=fastline1.sharepoint.com
# SP_SITE_PATH=/sites/flg
# SP_DOCLIB=Shared Documents


# ------------------------
# app.py (single file app)
# ------------------------

import os
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass

from flask import Flask, request, jsonify, abort
from dotenv import load_dotenv
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from apscheduler.schedulers.background import BackgroundScheduler
from tenacity import retry, wait_exponential, stop_after_attempt

import requests

# --- GoHighLevel OAuth Token Management ---
GHL_CLIENT_ID = os.getenv("GHL_CLIENT_ID", "")
GHL_CLIENT_SECRET = os.getenv("GHL_CLIENT_SECRET", "")
GHL_OAUTH_TOKEN_URL = "https://marketplace.leadconnectorhq.com/oauth/token"

_ghl_token_cache = {"access_token": None, "expires_at": None}

def get_ghl_oauth_token():
    now = datetime.utcnow()
    if _ghl_token_cache["access_token"] and _ghl_token_cache["expires_at"] > now:
        return _ghl_token_cache["access_token"]
    data = {
        "grant_type": "client_credentials",
        "client_id": GHL_CLIENT_ID,
        "client_secret": GHL_CLIENT_SECRET,
        "scope": "locations.readonly contacts.readonly opportunities.readonly conversations.readonly"
    }
    resp = requests.post(GHL_OAUTH_TOKEN_URL, data=data, timeout=30)
    resp.raise_for_status()
    tok = resp.json()
    _ghl_token_cache["access_token"] = tok["access_token"]
    _ghl_token_cache["expires_at"] = now + timedelta(seconds=tok.get("expires_in", 3600) - 60)
    return tok["access_token"]

# ---------- Load env
load_dotenv()

PORT = int(os.getenv("PORT", 5000))
X_API_KEY = os.getenv("X_API_KEY", "")
SYNC_API_KEY = os.getenv("SYNC_API_KEY", X_API_KEY)
DB_URL = os.getenv("DB_URL", "sqlite:///ghl_sync.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

GHL_BASE_URL = os.getenv("GHL_BASE_URL", "https://rest.gohighlevel.com/v1")
GHL_API_KEY = os.getenv("GHL_API_KEY", "")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID", "")

MS_TENANT_ID = os.getenv("MS_TENANT_ID")
MS_CLIENT_ID = os.getenv("MS_CLIENT_ID")
MS_CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET")
MS_SENDER = os.getenv("MS_SENDER", "sales@fastlinegroup.com")

SP_SITE_HOST = os.getenv("SP_SITE_HOST", "fastline1.sharepoint.com")
SP_SITE_PATH = os.getenv("SP_SITE_PATH", "/sites/flg")
SP_DOCLIB = os.getenv("SP_DOCLIB", "Shared Documents")

# ---------- Logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO),
                    format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger("ghl-sync")

# ---------- DB setup
class Base(DeclarativeBase):
    pass

class SyncLog(Base):
    __tablename__ = "sync_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    finished_at: Mapped[datetime | None]
    scope: Mapped[str] = mapped_column(default="contacts")  # contacts|opportunities|orders|webhook
    status: Mapped[str] = mapped_column(default="running")   # running|success|error
    items: Mapped[int] = mapped_column(default=0)
    message: Mapped[str] = mapped_column(default="")

class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    event_type: Mapped[str]
    payload_json: Mapped[str]
    processed: Mapped[bool] = mapped_column(default=False)
    error: Mapped[str] = mapped_column(default="")

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    ghl_contact_id: Mapped[str] = mapped_column(default="")
    customer_email: Mapped[str] = mapped_column(default="")
    customer_name: Mapped[str] = mapped_column(default="")
    total: Mapped[float] = mapped_column(default=0.0)
    currency: Mapped[str] = mapped_column(default="GBP")
    pdf_path: Mapped[str] = mapped_column(default="")
    sharepoint_url: Mapped[str] = mapped_column(default="")
    status: Mapped[str] = mapped_column(default="pending")  # pending|emailed|archived

# Engine + Session
engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# ---------- Flask
app = Flask(__name__)


# ---------- Utilities

def require_api_key(header_name: str, expected: str):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            key = request.headers.get(header_name, "")
            if expected and key != expected:
                abort(403)
            return fn(*args, **kwargs)
        wrapper.__name__ = fn.__name__
        return wrapper
    return decorator


# ---------- GHL Client (minimal, extend as needed)
class GHLClient:
    def get_conversations(self, location_id: str, page=1, limit=100, access_token: str = None):
        """
        Conversations live on the LeadConnector services API rather than the legacy /v1 endpoint.
        """
        params = {"locationId": location_id, "page": page, "limit": limit}
        token = access_token if access_token else self.api_key
        headers = {
            "Authorization": f"Bearer {token}",
            "Version": "2021-07-28",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Location-Id": location_id,
        }
        url = "https://services.leadconnectorhq.com/conversations/search"
        r = requests.get(url, params=params, headers=headers, timeout=60)
        r.raise_for_status()
        return r.json()
    def __init__(self, api_key: str, base_url: str = GHL_BASE_URL):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })

    @retry(wait=wait_exponential(multiplier=1, min=1, max=20), stop=stop_after_attempt(5))
    def get_contacts(self, page=1, limit=100, updated_since: datetime | None = None):
        params = {"page": page, "limit": limit}
        if updated_since:
            # GHL typically expects ISO8601; adjust if your account requires a different param name
            params["updatedAt[gte]"] = updated_since.isoformat()
        url = f"{self.base_url}/contacts/"
        r = self.session.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    @retry(wait=wait_exponential(multiplier=1, min=1, max=20), stop=stop_after_attempt(5))
    def get_opportunities(self, location_id: str, page=1, limit=100):
        params = {"locationId": location_id, "page": page, "limit": limit}
        url = f"{self.base_url}/opportunities/"
        r = self.session.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def create_note(self, contact_id: str, body: str):
        url = f"{self.base_url}/contacts/{contact_id}/notes/"
        payload = {"body": body}
        r = self.session.post(url, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()


# ---------- Microsoft Graph helpers (SharePoint + Email)
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

@dataclass
class GraphToken:
    access_token: str
    expires_at: datetime

_graph_cache: GraphToken | None = None

def _get_graph_token() -> str:
    # simple in-memory token cache using client credentials
    global _graph_cache
    if _graph_cache and _graph_cache.expires_at > datetime.utcnow() + timedelta(minutes=2):
        return _graph_cache.access_token

    token_url = f"https://login.microsoftonline.com/{MS_TENANT_ID}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": MS_CLIENT_ID,
        "client_secret": MS_CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default"
    }
    resp = requests.post(token_url, data=data, timeout=30)
    resp.raise_for_status()
    tok = resp.json()
    _graph_cache = GraphToken(
        access_token=tok["access_token"],
        expires_at=datetime.utcnow() + timedelta(seconds=int(tok.get("expires_in", 3600)))
    )
    return _graph_cache.access_token


def upload_to_sharepoint(file_path: str, dest_folder: str = "Orders") -> str:
    """Upload a file to SharePoint doc library and return webUrl."""
    access_token = _get_graph_token()
    # Resolve site & drive
    site_url = f"https://graph.microsoft.com/v1.0/sites/{SP_SITE_HOST}:{SP_SITE_PATH}"
    site = requests.get(site_url, headers={"Authorization": f"Bearer {access_token}"}, timeout=30).json()
    site_id = site.get("id")

    drive = requests.get(
        f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives", 
        headers={"Authorization": f"Bearer {access_token}"}, timeout=30).json()
    drive_id = None
    for d in drive.get("value", []):
        if d.get("name") == SP_DOCLIB:
            drive_id = d.get("id")
            break
    if not drive_id:
        raise RuntimeError("Doc library not found")

    # Ensure dest folder
    folder_url = f"/Orders/{datetime.utcnow().strftime('%Y/%m/%d')}" if dest_folder == "Orders" else f"/{dest_folder}"
    ensure = requests.post(
        f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:{folder_url}",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        json={"folder": {}, "@microsoft.graph.conflictBehavior": "retain"}, timeout=30)
    if ensure.status_code not in (200, 201):
        logger.warning("Ensure folder status %s: %s", ensure.status_code, ensure.text)

    # Upload file
    name = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        upload = requests.put(
            f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:{folder_url}/{name}:/content",
            headers={"Authorization": f"Bearer {access_token}"}, data=f, timeout=120)
    upload.raise_for_status()
    meta = upload.json()
    return meta.get("webUrl", "")


def send_email_via_graph(to: list[str], subject: str, html_body: str, attachments: list[tuple[str, bytes]] | None = None):
    access_token = _get_graph_token()
    msg = {
        "message": {
            "subject": subject,
            "body": {"contentType": "HTML", "content": html_body},
            "toRecipients": [{"emailAddress": {"address": addr}} for addr in to],
        },
        "saveToSentItems": True
    }
    # file attachments (under 3MB recommended for simple base64 payload)
    if attachments:
        import base64
        msg["message"]["attachments"] = []
        for filename, content in attachments:
            b64 = base64.b64encode(content).decode("utf-8")
            msg["message"]["attachments"].append({
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": filename,
                "contentType": "application/pdf",
                "contentBytes": b64
            })

    url = f"https://graph.microsoft.com/v1.0/users/{MS_SENDER}/sendMail"
    r = requests.post(url, headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}, json=msg, timeout=30)
    if r.status_code not in (202, 200):
        logger.error("Graph sendMail error %s %s", r.status_code, r.text)
        r.raise_for_status()


# ---------- PDF generator

def generate_order_pdf(order: Order) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    text = c.beginText(40, 800)
    text.textLine("Fastline Group – Order Confirmation")
    text.textLine("")
    text.textLine(f"Order ID: {order.id}")
    text.textLine(f"Customer: {order.customer_name} <{order.customer_email}>")
    text.textLine(f"Total: {order.total} {order.currency}")
    text.textLine(f"Date: {order.created_at.strftime('%Y-%m-%d %H:%M UTC')}")
    c.drawText(text)
    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()


def load_cached_oauth_token() -> str | None:
    """Try to load a stored OAuth access token for the default account."""
    candidate_paths = [
        os.path.join(os.getcwd(), "ghl-custom-frontend", "data", "oauth_tokens.json"),
        os.path.join(os.getcwd(), "data", "oauth_tokens.json"),
    ]
    for p in candidate_paths:
        try:
            if not os.path.exists(p):
                continue
            with open(p, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            # Prefer token stored under known user keys
            for key in ("default", "jon"):
                token = data.get(key, {}).get("accessToken")
                if token:
                    return token
            # Fallback: search any entry with accessToken
            for entry in data.values():
                if isinstance(entry, dict) and entry.get("accessToken"):
                    return entry["accessToken"]
        except Exception as exc:
            logger.warning("Failed to load cached OAuth token from %s: %s", p, exc)
    return None


# ---------- Sync + Webhook logic

def run_conversations_sync(location_id: str, access_token: str = None) -> dict:
    """Fetch GHL conversations and save to FastlineSync/conversations-<locationId>.json"""
    import os
    import json
    import logging
    logger = logging.getLogger("ghl-sync")
    sync_dir = os.path.join(os.getcwd(), "ghl-custom-frontend", "FastlineSync")
    os.makedirs(sync_dir, exist_ok=True)
    all_conversations = []
    page = 1
    try:
        # Try provided token, then cached, then fresh OAuth
        token_to_use = access_token or load_cached_oauth_token()
        if not token_to_use:
            token_to_use = get_ghl_oauth_token()
        while True:
            data = ghl.get_conversations(location_id, page=page, limit=100, access_token=token_to_use)
            items = data.get("conversations") or data.get("items") or []
            all_conversations.extend(items)
            if not items or len(items) < 100:
                break
            page += 1
        file_path = os.path.join(sync_dir, f"conversations-{location_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(all_conversations, f, ensure_ascii=False, indent=2)
        logger.info("Fetched %s conversations for location %s", len(all_conversations), location_id)
        return {"synced": len(all_conversations), "file": file_path}
    except Exception as e:
        logger.exception("Conversations sync failed for location %s", location_id)
        return {"error": str(e)}

ghl = GHLClient(GHL_API_KEY, GHL_BASE_URL)


def run_contacts_sync(updated_since: datetime | None = None) -> dict:
    sess = SessionLocal()
    log = SyncLog(scope="contacts", status="running")
    sess.add(log)
    sess.commit()

    try:
        page = 1
        total = 0
        while True:
            data = ghl.get_contacts(page=page, limit=100, updated_since=updated_since)
            items = data.get("contacts") or data.get("items") or []
            total += len(items)
            logger.info("Fetched %s contacts on page %s", len(items), page)
            if not items or len(items) < 100:
                break
            page += 1

        log.status = "success"
        log.items = total
        log.finished_at = datetime.utcnow()
        sess.commit()
        return {"synced": total}
    except Exception as e:
        logger.exception("Contact sync failed")
        log.status = "error"
        log.message = str(e)
        log.finished_at = datetime.utcnow()
        sess.commit()
        return {"error": str(e)}
    finally:
        sess.close()


def process_webhook(event_type: str, payload: dict) -> None:
    """Minimal example: capture events and create orders on a specific event type."""
    sess = SessionLocal()
    try:
        # Persist raw event
        wh = WebhookEvent(event_type=event_type, payload_json=json.dumps(payload))
        sess.add(wh)
        sess.commit()

        # Example: suppose GHL posts an "order.created" type (adjust to your actual payload)
        if event_type.lower() in {"order.created", "invoice.payment_succeeded", "checkout.order.created"}:
            customer_email = payload.get("customer", {}).get("email", "") or payload.get("contact", {}).get("email", "")
            customer_name = payload.get("customer", {}).get("name", "") or payload.get("contact", {}).get("name", "")
            ghl_contact_id = str(payload.get("contact", {}).get("id", ""))
            amount = float(payload.get("amount_total", payload.get("total", 0))) / (100.0 if payload.get("amount_total") else 1.0)
            currency = (payload.get("currency") or "GBP").upper()

            order = Order(
                ghl_contact_id=ghl_contact_id,
                customer_email=customer_email,
                customer_name=customer_name,
                total=amount,
                currency=currency,
                status="pending",
            )
            sess.add(order)
            sess.commit()  # get order.id for PDF

            # Generate PDF
            pdf_bytes = generate_order_pdf(order)
            pdf_name = f"Order-{order.id}.pdf"
            pdf_path = os.path.join(os.getcwd(), "data", pdf_name)
            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
            with open(pdf_path, "wb") as f:
                f.write(pdf_bytes)

            # Upload to SharePoint (per Jon's requirement)
            try:
                sp_url = upload_to_sharepoint(pdf_path, dest_folder="Orders")
            except Exception as e:
                logger.error("SharePoint upload failed: %s", e)
                sp_url = ""

            order.pdf_path = pdf_path
            order.sharepoint_url = sp_url
            sess.commit()

            # Email customer (and CC internal if desired)
            subject = "Your Fastline Order Confirmation"
            html = f"""
                <p>Hi {customer_name or 'there'},</p>
                <p>Thanks for your order with Fastline Group. Your confirmation is attached.</p>
                <p>You can also view it on SharePoint (internal): {sp_url or '—'}</p>
                <p>Cheers,<br/>Fastline Team</p>
            """
            try:
                send_email_via_graph([customer_email] if customer_email else [MS_SENDER], subject, html, attachments=[(pdf_name, pdf_bytes)])
                order.status = "emailed"
                sess.commit()
            except Exception as e:
                logger.error("Email send failed: %s", e)

            wh.processed = True
            sess.commit()

    except Exception as e:
        logger.exception("Webhook processing failed")
        if 'wh' in locals():
            wh.error = str(e)
            sess.commit()
    finally:
        sess.close()


# ---------- Routes

@app.get("/healthz")
def healthz():
    return {"ok": True, "time": datetime.utcnow().isoformat()}


@app.post("/sync/ghl")
@require_api_key("x-api-key", SYNC_API_KEY)
def sync_ghl():
    """Manual sync trigger. Optionally pass updated_since (ISO8601) and access_token in JSON."""
    body = request.get_json(silent=True) or {}
    ts = body.get("updated_since")
    updated_since = None
    if ts:
        try:
            updated_since = datetime.fromisoformat(ts)
        except Exception:
            pass
    access_token = body.get("access_token")
    contacts_result = run_contacts_sync(updated_since)
    conversations_result = run_conversations_sync(GHL_LOCATION_ID, access_token=access_token)
    return jsonify({
        "contacts": contacts_result,
        "conversations": conversations_result
    })


@app.post("/webhooks/ghl")
def webhook_ghl():
    # If GHL supports a signature header for verification, add verification here.
    event_type = request.headers.get("X-Event-Type") or (request.json or {}).get("event") or "unknown"
    payload = request.json or {}
    logger.info("Webhook: %s", event_type)
    process_webhook(event_type, payload)
    return {"received": True}


@app.post("/orders")
@require_api_key("x-api-key", X_API_KEY)
def create_order():
    body = request.get_json(force=True)
    email = body.get("customer_email")
    name = body.get("customer_name", "")
    total = float(body.get("total", 0))
    currency = body.get("currency", "GBP").upper()
    contact_id = str(body.get("ghl_contact_id", ""))

    sess = SessionLocal()
    try:
        order = Order(
            ghl_contact_id=contact_id,
            customer_email=email,
            customer_name=name,
            total=total,
            currency=currency,
        )
        sess.add(order)
        sess.commit()

        pdf_bytes = generate_order_pdf(order)
        pdf_name = f"Order-{order.id}.pdf"
        pdf_path = os.path.join(os.getcwd(), "data", pdf_name)
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)

        # Upload to SharePoint
        sp_url = ""
        try:
            sp_url = upload_to_sharepoint(pdf_path, dest_folder="Orders")
        except Exception as e:
            logger.error("SharePoint upload failed: %s", e)

        order.pdf_path = pdf_path
        order.sharepoint_url = sp_url
        order.status = "pending"
        sess.commit()

        # Email
        subject = "Your Fastline Order Confirmation"
        html = f"<p>Hi {name or 'there'},</p><p>Your order is attached.</p>"
        try:
            send_email_via_graph([email] if email else [MS_SENDER], subject, html, attachments=[(pdf_name, pdf_bytes)])
            order.status = "emailed"
            sess.commit()
        except Exception as e:
            logger.error("Email send failed: %s", e)

        return {"ok": True, "order_id": order.id, "sharepoint_url": sp_url}
    finally:
        sess.close()


# ---------- Scheduler (30‑minute sync)

def scheduled_sync():
    # Last 2 hours incremental window, adjust as needed
    updated_since = datetime.utcnow() - timedelta(hours=2)
    run_contacts_sync(updated_since)
    run_conversations_sync(GHL_LOCATION_ID)

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(scheduled_sync, 'interval', minutes=30)


# ---------- Main
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--init-db", action="store_true")
    args = parser.parse_args()

    if args.init_db:
        Base.metadata.create_all(engine)
        print("DB initialized at:", DB_URL)
    else:
        # Ensure DB exists
        Base.metadata.create_all(engine)
        scheduler.start()
        app.run(host="0.0.0.0", port=PORT)
