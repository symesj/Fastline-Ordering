@echo off
REM === Start Fastline Flask API ===
setlocal

REM Adjust these if your paths differ
set APP_DIR=C:\Users\fladmin\Documents\flask_app
set VENV=%APP_DIR%\venv

cd /d %APP_DIR%

REM Activate venv (if you use one); if not, you can remove the next line
call "%VENV%\Scripts\activate.bat"

REM Ensure .env is picked up by app.py (you already added load_dotenv())
REM Run the app bound to all interfaces on port 5000
python app.py
