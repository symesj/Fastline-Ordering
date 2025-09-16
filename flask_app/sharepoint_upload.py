# sharepoint_upload.py
import os
import requests

# ----------------- Config (defaults match your tenant) -----------------
SP_HOSTNAME   = os.getenv("SP_HOSTNAME",   "fastline1.sharepoint.com")
SP_SITE_PATH  = os.getenv("SP_SITE_PATH",  "/flg")               # accepts "/flg" or "/sites/flg"
SP_DRIVE_NAME = os.getenv("SP_DRIVE_NAME", "Shared Documents")   # exact doc library name
GRAPH = "https://graph.microsoft.com/v1.0"
# ----------------------------------------------------------------------

# Reuse the Graph token from your email module
from graph_mail import _token


def _headers(token: str, json_ct: bool = True):
    h = {"Authorization": f"Bearer {token}"}
    if json_ct:
        h["Content-Type"] = "application/json"
    return h


def _normalize_site_segment(site_path: str) -> str:
    """
    Accept either "/flg" or "/sites/flg" and return exactly "/sites/flg"
    """
    p = (site_path or "").strip()
    if not p.startswith("/"):
        p = "/" + p
    if p.startswith("/sites/"):
        return p
    return "/sites" + p


def _resolve_site_id(token: str) -> str:
    """
    Resolve the SharePoint site ID from hostname + site path.
    """
    site_segment = _normalize_site_segment(SP_SITE_PATH)
    url = f"{GRAPH}/sites/{SP_HOSTNAME}:{site_segment}?$select=id,name,webUrl"
    r = requests.get(url, headers=_headers(token, json_ct=False), timeout=30)
    r.raise_for_status()
    return r.json()["id"]


def _resolve_drive_id(token: str, site_id: str) -> str:
    """
    Resolve the document library (drive) ID. Prefer exact name match; fallback to any doc library.
    """
    url = f"{GRAPH}/sites/{site_id}/drives?$select=id,name,driveType"
    r = requests.get(url, headers=_headers(token, json_ct=False), timeout=30)
    r.raise_for_status()
    drives = r.json().get("value", [])
    # Prefer exact (case-insensitive) name match
    for d in drives:
        if d.get("name", "").lower() == SP_DRIVE_NAME.lower():
            return d["id"]
    # Fallback to first document library
    for d in drives:
        if d.get("driveType") == "documentLibrary":
            return d["id"]
    raise RuntimeError("Could not find a SharePoint document library drive.")


def _relative_to_library(folder_path: str) -> str:
    """
    Return a path RELATIVE to the library root.
    If the caller includes the library name as the first segment (e.g. 'Shared Documents/...'),
    strip it so we don't create 'Shared Documents/Shared Documents/...'.
    """
    parts = [p for p in (folder_path or "").split("/") if p]
    if parts and parts[0].lower() == SP_DRIVE_NAME.lower():
        parts = parts[1:]
    return "/".join(parts)


def _ensure_folder_path(token: str, site_id: str, drive_id: str, folder_path: str) -> str:
    """
    Ensure each folder in folder_path exists. Returns the final folder's driveItem id.
    'folder_path' may include or omit the library name; this function normalizes it.
    """
    relative = _relative_to_library(folder_path)
    parts = [p for p in relative.split("/") if p]

    # Library root
    rroot = requests.get(
        f"{GRAPH}/sites/{site_id}/drives/{drive_id}/root",
        headers=_headers(token, json_ct=False),
        timeout=30,
    )
    rroot.raise_for_status()
    parent_id = rroot.json()["id"]

    for name in parts:
        # List children of current folder
        rc = requests.get(
            f"{GRAPH}/sites/{site_id}/drives/{drive_id}/items/{parent_id}/children?$select=id,name,folder",
            headers=_headers(token, json_ct=False),
            timeout=30,
        )
        rc.raise_for_status()
        kids = rc.json().get("value", [])
        found = next((c for c in kids if c.get("name") == name and c.get("folder")), None)
        if found:
            parent_id = found["id"]
            continue

        # Create folder if missing
        create_url = f"{GRAPH}/sites/{site_id}/drives/{drive_id}/items/{parent_id}/children"
        body = {"name": name, "folder": {}, "@microsoft.graph.conflictBehavior": "replace"}
        cr = requests.post(create_url, headers=_headers(token), json=body, timeout=30)
        cr.raise_for_status()
        parent_id = cr.json()["id"]

    return parent_id


def _upload_small(token: str, site_id: str, drive_id: str, folder_path: str, local_path: str, dest_filename: str) -> dict:
    """
    For files <= 4 MB: single PUT to the path under the library root.
    """
    relative = _relative_to_library(folder_path)
    target = f"{relative}/{dest_filename}" if relative else dest_filename
    url = f"{GRAPH}/sites/{site_id}/drives/{drive_id}/root:/{target}:/content"
    with open(local_path, "rb") as f:
        r = requests.put(url, headers={"Authorization": f"Bearer {token}"}, data=f, timeout=300)
    r.raise_for_status()
    return r.json()


def _upload_large(token: str, site_id: str, drive_id: str, folder_path: str, local_path: str, dest_filename: str) -> dict:
    """
    For files > 4 MB: create an upload session and send in 5 MB chunks.
    """
    relative = _relative_to_library(folder_path)
    target = f"{relative}/{dest_filename}" if relative else dest_filename

    # Create upload session
    url = f"{GRAPH}/sites/{site_id}/drives/{drive_id}/root:/{target}:/createUploadSession"
    body = {"item": {"@microsoft.graph.conflictBehavior": "replace"}}
    r = requests.post(url, headers=_headers(token), json=body, timeout=60)
    r.raise_for_status()
    upload_url = r.json()["uploadUrl"]

    CHUNK = 5 * 1024 * 1024
    size = os.path.getsize(local_path)
    sent = 0
    with open(local_path, "rb") as f:
        while sent < size:
            chunk = f.read(CHUNK)
            if not chunk:
                break
            start = sent
            end = sent + len(chunk) - 1
            rr = requests.put(
                upload_url,
                headers={
                    "Content-Length": str(len(chunk)),
                    "Content-Range": f"bytes {start}-{end}/{size}",
                },
                data=chunk,
                timeout=300,
            )
            if rr.status_code not in (200, 201, 202):
                raise RuntimeError(f"Chunk upload failed: {rr.status_code} {rr.text}")
            sent = end + 1
            if rr.status_code in (200, 201):
                return rr.json()

    # Fallback: fetch the item by path
    gi = requests.get(
        f"{GRAPH}/sites/{site_id}/drives/{drive_id}/root:/{target}",
        headers=_headers(token, json_ct=False),
        timeout=30,
    )
    gi.raise_for_status()
    return gi.json()


def upload_to_sharepoint(local_path: str, folder_path: str, dest_filename: str | None = None) -> str:
    """
    Upload a local file into SharePoint.
    - 'folder_path' can include or omit the doc library name; both work.
    - Returns the webUrl of the uploaded item.
    """
    if not os.path.exists(local_path):
        raise FileNotFoundError(local_path)
    if dest_filename is None:
        dest_filename = os.path.basename(local_path)

    token = _token()
    site_id = _resolve_site_id(token)
    drive_id = _resolve_drive_id(token, site_id)

    _ensure_folder_path(token, site_id, drive_id, folder_path)

    size = os.path.getsize(local_path)
    if size <= 4 * 1024 * 1024:
        item = _upload_small(token, site_id, drive_id, folder_path, local_path, dest_filename)
    else:
        item = _upload_large(token, site_id, drive_id, folder_path, local_path, dest_filename)

    return item.get("webUrl", "")
