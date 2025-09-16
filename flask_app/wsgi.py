# wsgi.py
"""
WSGI entrypoint for production.
- Exposes `app` for servers like Waitress:  python -m waitress --host=0.0.0.0 --port=5000 wsgi:app
- Loads .env so secrets are available when run as a Windows service.
- Adds a lightweight /health endpoint for monitoring and quick curl checks.
"""

from dotenv import load_dotenv
load_dotenv()  # reads .env from the current directory, if present

# --- Import your Flask app ---
# If your app instance lives in app.py as `app`, this line is correct:
from app import app  # DO NOT rename; Waitress expects "app" here

# If you use an application factory pattern instead (e.g., create_app()),
# replace the line above with:
# from app import create_app
# app = create_app()

# --- Optional: simple health route (safe to re-import) ---
try:
    @app.get("/health")
    def health():
        return {"ok": True}, 200
except Exception:
    # If the route already exists in your app, ignore redefinition.
    pass


# --- Local dev runner (not used by Waitress/NSSM) ---
if __name__ == "__main__":
    # Bind to all interfaces for testing; turn off debug in production.
    app.run(host="0.0.0.0", port=5000, debug=False)
