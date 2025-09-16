from graph_mail import _token
import os, requests
t=_token()
site_url=f"https://graph.microsoft.com/v1.0/sites/{os.getenv('SP_HOSTNAME')}:/sites{os.getenv('SP_SITE_PATH') if os.getenv('SP_SITE_PATH','/').startswith('/sites/') else '/sites'+os.getenv('SP_SITE_PATH','/')}"
site=requests.get(site_url, headers={"Authorization":f"Bearer {t}"}, timeout=30).json()
drives=requests.get(f"https://graph.microsoft.com/v1.0/sites/{site['id']}/drives?$select=id,name,driveType",
                    headers={"Authorization":f"Bearer {t}"}, timeout=30).json()
print(drives)
