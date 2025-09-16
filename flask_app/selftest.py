import os, traceback
from graph_mail import send_mail_from_sales

print("Tenant set:", bool(os.getenv("GRAPH_TENANT_ID")))
print("Client set:", bool(os.getenv("GRAPH_CLIENT_ID")))
print("Secret set:", bool(os.getenv("GRAPH_CLIENT_SECRET")))

try:
    send_mail_from_sales(
        to_email="john.symes@fastlinegroup.com",
        subject="Self-test",
        html_body="<p>Self-test</p>",
        from_user_upn="orders@fastlinegroup.com",
    )
    print("OK: send_mail_from_sales returned without exception")
except Exception as e:
    print("FAILED:", e)
    traceback.print_exc()
