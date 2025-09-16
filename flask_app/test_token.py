import os, requests
t=os.getenv("MS_TENANT_ID"); c=os.getenv("MS_CLIENT_ID"); s=os.getenv("MS_CLIENT_SECRET")
print("Tenant:", t); print("Client:", c); print("Secret set:", bool(s))
r=requests.post(f"https://login.microsoftonline.com/{t}/oauth2/v2.0/token",
    data={"client_id":c,"client_secret":s,"scope":"https://graph.microsoft.com/.default","grant_type":"client_credentials"},
    timeout=30)
print("Status:", r.status_code)
print(r.text[:300])
