import os, json
import requests
from pathlib import Path
from typing import Optional, Tuple

TENANT_ID = os.getenv("MS_TENANT_ID", "")
CLIENT_ID = os.getenv("MS_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET", "")

# Example:
#   SP_SITE_HOSTNAME = "fastline1.sharepoint.com"
#   SP_SITE_PATH = "/sites/flg"
SP_SITE_HOSTNAME = os.getenv("SP_SITE_HOSTNAME", "")
SP_SITE_PATH = os.getenv("SP_SITE_PATH", "/sites/flg")

# Document library / drive to use (usually "Documents" == "Shared Documents")
SP_DRIVE_NAME = os.getenv("SP_DRIVE_NAME", "Documents")  # internal drive name

class GraphError(Exception):
    pass

def _token() -> str:
    if not (TENANT_ID and CLIENT_ID and CLIENT_SECRET):
        raise GraphError("Missing Graph app credentials (MS_TENANT_ID / MS_CLIENT_ID / MS_CLIENT_SECRET).")
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default"
    }
    r = requests.post(url, data=data)
    if not r.ok:
        raise GraphError(f"Auth failed: {r.status_code} {r.text}")
    return r.json()["access_token"]

def _headers() -> dict:
    return {"Authorization": f"Bearer {_token()}"}

def get_site_id() -> str:
    # GET /sites/{hostname}:{site-path}
    url = f"https://graph.microsoft.com/v1.0/sites/{SP_SITE_HOSTNAME}:{SP_SITE_PATH}"
    r = requests.get(url, headers=_headers())
    if not r.ok:
        raise GraphError(f"Get site failed: {r.status_code} {r.text}")
    return r.json()["id"]

def get_drive_id(site_id: str, drive_name: str = SP_DRIVE_NAME) -> str:
    # GET /sites/{site-id}/drives
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
    r = requests.get(url, headers=_headers())
    if not r.ok:
        raise GraphError(f"List drives failed: {r.status_code} {r.text}")
    for d in r.json().get("value", []):
        if d.get("name") == drive_name or d.get("driveType") == "documentLibrary":
            # Prefer exact name; fallback first doc library
            if d.get("name") == drive_name:
                return d["id"]
            drive_id = d["id"]
    if 'drive_id' in locals():
        return drive_id
    raise GraphError(f"Drive '{drive_name}' not found.")

def upload_file_to_sharepoint(local_path: str, sp_folder: str) -> Tuple[str, str]:
    """
    Upload local file to SharePoint and return (driveItemId, webUrl)
    sp_folder example: 'Shared Documents/Orders/FLG-20250915-ABCD1234'
    If 'Shared Documents' is mapped to drive root, you can pass just 'Orders/...'
    """
    path = Path(local_path)
    if not path.exists():
        raise GraphError(f"Local file not found: {local_path}")

    site_id = get_site_id()
    drive_id = get_drive_id(site_id)

    # Normalize folder path inside the drive
    sp_folder = sp_folder.strip("/")

    # Create folder chain if needed using /root:/path:/children
    # We will upload using the simple-upload (PUT) to: /root:/{folder}/{filename}:/content
    upload_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{sp_folder}/{path.name}:/content"

    with open(path, "rb") as f:
        r = requests.put(upload_url, headers=_headers(), data=f)
    if not r.ok:
        raise GraphError(f"Upload failed: {r.status_code} {r.text}")

    item = r.json()
    return item["id"], item.get("webUrl", "")
