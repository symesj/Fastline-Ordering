# test_route_upload.py
from smart_routing import upload_pdf_with_routing

files = [
    r"C:\Users\fladmin\Documents\flask_app\data\Quote-5678.pdf",   # → Quotes 2025/Month
    r"C:\Users\fladmin\Documents\flask_app\data\Order-1234.pdf",   # → Orders 2025/Month
    r"C:\Users\fladmin\Documents\flask_app\data\INV-9999.pdf",     # → Invoice YYYY/Month
    r"C:\Users\fladmin\Documents\flask_app\data\Misc-Note.pdf"     # → Base Admin folder
]

for p in files:
    try:
        url = upload_pdf_with_routing(p)
        print(p, "→", url)
    except Exception as e:
        print(p, "ERROR:", e)
