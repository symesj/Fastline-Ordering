from graph_mail import _token
import os, requests

t = _token()

site_path = os.getenv("SP_SITE_PATH", "/flg")
if not site_path.startswith("/"):
    site_path = "/" + site_path
site_segment = site_path if site_path.startswith("/sites/") else "/sites" + site_path

url = f"https://graph.microsoft.com/v1.0/sites/{os.getenv('SP_HOSTNAME')}:{site_segment}?$select=id,name,webUrl"
r = requests.get(url, headers={"Authorization": f"Bearer {t}"}, timeout=30)

print("URL:", url)
print("Status:", r.status_code)
print(r.text[:400])
