import os, requests

tenant = os.getenv("GRAPH_TENANT_ID")
client = os.getenv("GRAPH_CLIENT_ID")
secret = os.getenv("GRAPH_CLIENT_SECRET")

print("Tenant:", tenant)
print("Client:", client)
print("Secret starts with:", secret[:5], "...")

url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
data = {
    "client_id": client,
    "client_secret": secret,
    "grant_type": "client_credentials",
    "scope": "https://graph.microsoft.com/.default",
}
r = requests.post(url, data=data, timeout=30)
print("Status:", r.status_code)
print("Response:", r.json())
