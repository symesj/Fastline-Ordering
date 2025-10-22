@echo off
title Fastline Ordering - Server Launcher
color 0A

echo ========================================
echo    Fastline Ordering Server Launcher
echo ========================================
echo.

REM Get the directory where this batch file is located
set BATCH_DIR=%~dp0
echo Batch file location: %BATCH_DIR%

REM Set paths relative to batch file location
set FLASK_DIR=%BATCH_DIR%flask_app
set NEXTJS_DIR=%BATCH_DIR%ghl-custom-frontend

echo Flask directory: %FLASK_DIR%
echo Next.js directory: %NEXTJS_DIR%
echo.

REM Check if directories exist
if not exist "%FLASK_DIR%" (
    echo ERROR: Flask directory not found: %FLASK_DIR%
    pause
    exit /b 1
)

if not exist "%NEXTJS_DIR%" (
    echo ERROR: Next.js directory not found: %NEXTJS_DIR%
    pause
    exit /b 1
)

echo Starting servers...
echo.

REM Start Flask server in a new window
echo [1/2] Starting Flask API server (Port 5000)...
start "Flask API Server - Port 5000" cmd /k "cd /d "%FLASK_DIR%" && python app_orders.py"

REM Wait a moment for Flask to start
timeout /t 3 /nobreak >nul

REM Start Next.js server in a new window  
echo [2/2] Starting Next.js frontend server (Port 3000)...
start "Next.js Frontend - Port 3000" cmd /k "cd /d "%NEXTJS_DIR%" && npm run dev"

echo.
echo ========================================
echo  Both servers are starting up!
echo ========================================
echo  Flask API:     http://localhost:5000
echo  Next.js App:   http://localhost:3000
echo ========================================
echo.
echo Press any key to close this launcher...
echo (The servers will continue running in their own windows)
pause >nul