# graph_mail.py
import os
import json
import requests

# Allow GUID, domain, or fallback to 'organizations'
TENANT_ID = os.getenv("MS_TENANT_ID", "organizations")
CLIENT_ID = os.getenv("MS_CLIENT_ID")
CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET")

GRAPH_SCOPE = "https://graph.microsoft.com/.default"
AUTH_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
GRAPH = "https://graph.microsoft.com/v1.0"


def _token() -> str:
    if not (CLIENT_ID and CLIENT_SECRET):
        raise RuntimeError("Missing MS_CLIENT_ID / MS_CLIENT_SECRET env vars")
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": GRAPH_SCOPE,
        "grant_type": "client_credentials",
    }
    r = requests.post(AUTH_URL, data=data, timeout=30)
    if r.status_code >= 400:
        raise RuntimeError(f"Token request failed: {r.status_code} {r.text}")
    return r.json()["access_token"]


def send_email_via_graph(to: str, subject: str, html_body: str, attachments: list[dict] | None, from_user: str):
    token = _token()
    url = f"{GRAPH}/users/{from_user}/sendMail"
    attach_payload = []
    for a in attachments or []:
        attach_payload.append({
            "@odata.type": "#microsoft.graph.fileAttachment",
            "name": a["name"],
            "contentType": a.get("contentType", "application/octet-stream"),
            "contentBytes": a["contentBytes_b64"],
        })
    body = {
        "message": {
            "subject": subject,
            "body": {"contentType": "HTML", "content": html_body},
            "toRecipients": [{"emailAddress": {"address": to}}],
            "attachments": attach_payload
        },
        "saveToSentItems": True
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.post(url, headers=headers, data=json.dumps(body), timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"Graph sendMail failed: {r.status_code} {r.text}")
    return "sent"
