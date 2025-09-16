# smart_routing.py
import os, re
from datetime import datetime
from sharepoint_upload import upload_to_sharepoint

BASE_BUCKET = "Shared Documents/Sales/Admin"

def _ym(dt: datetime) -> tuple[str, str]:
    return dt.strftime("%Y"), dt.strftime("%B")

def _bucket_for_filename(filename: str, when: datetime) -> str:
    name = filename.lower()
    year, month = _ym(when)
    if "quote" in name:
        return f"{BASE_BUCKET}/1. Admin - Quote {year}/{month}"
    if "order" in name:
        return f"{BASE_BUCKET}/2. Admin - Order {year}/{month}"
    if re.search(r"\binv", name):  # catches inv, invoice, INV-123
        return f"{BASE_BUCKET}/3. Admin - Invoice/{year}/{month}"
    return BASE_BUCKET

def upload_pdf_with_routing(local_path: str, doc_date: datetime | None = None) -> str:
    if not os.path.exists(local_path):
        raise FileNotFoundError(local_path)
    dt = doc_date or datetime.now()
    folder = _bucket_for_filename(os.path.basename(local_path), dt)
    return upload_to_sharepoint(local_path, folder)
