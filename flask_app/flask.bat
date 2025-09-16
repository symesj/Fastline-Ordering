@echo off
setlocal enabledelayedexpansion

REM --- Paths ---
cd /d C:\Users\fladmin\Documents\flask_app

REM --- Ensure logs folder exists ---
if not exist logs mkdir logs

REM --- Use project venv ---
call ".\venv\Scripts\activate"

REM --- Helpful runtime env vars ---
set PYTHONUNBUFFERED=1
set FLASK_ENV=production
set FLASK_DEBUG=0
set PYTHONPATH=%CD%

REM --- Optional: load .env inside code (see wsgi.py) ---

REM --- Start via Waitress, bind to all interfaces on port 5000 ---
REM NOTE: wsgi:app expects a file "wsgi.py" exposing a variable named "app"
echo [%DATE% %TIME%] Starting Waitress... >> ".\logs\server.out"
python -m waitress --host=0.0.0.0 --port=5000 wsgi:app 1>>".\logs\server.out" 2>>".\logs\server.err"
