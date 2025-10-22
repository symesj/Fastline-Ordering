@echo off
setlocal enabledelayedexpansion

:: Set colors and title
title Fastline Ordering - Server Launcher
color 0A

cls
echo.
echo ==========================================
echo    🚀 Fastline Ordering Server Launcher
echo ==========================================
echo.

:: Get current directory
set "ROOT_DIR=%~dp0"
set "FLASK_DIR=%ROOT_DIR%flask_app"
set "NEXTJS_DIR=%ROOT_DIR%ghl-custom-frontend"
set "WHATSAPP_DIR=%NEXTJS_DIR%\whatsapp-web-service"

echo 📁 Project Root: %ROOT_DIR%
echo 🐍 Flask App:    %FLASK_DIR%
echo ⚛️  Next.js App:  %NEXTJS_DIR%
echo 💬 WhatsApp Service: %WHATSAPP_DIR%
echo.

:: Check directories
if not exist "%FLASK_DIR%" (
    echo ❌ ERROR: Flask directory not found!
    echo    Expected: %FLASK_DIR%
    echo.
    pause
    exit /b 1
)


if not exist "%NEXTJS_DIR%" (
    echo ❌ ERROR: Next.js directory not found!
    echo    Expected: %NEXTJS_DIR%
    echo.
    pause
    exit /b 1
)

if not exist "%WHATSAPP_DIR%" (
    echo ❌ ERROR: WhatsApp backend directory not found!
    echo    Expected: %WHATSAPP_DIR%
    echo.
    pause
    exit /b 1
)

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python not found. Please install Python first.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do set "PYTHON_VER=%%i"
    echo ✅ Python found: !PYTHON_VER!
)

:: Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Node.js not found. Please install Node.js first.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('node --version 2^>^&1') do set "NODE_VER=%%i"
    echo ✅ Node.js found: !NODE_VER!
)

echo.
echo 🚀 Starting servers...
echo.

:: Kill any existing processes first
echo 🔄 Cleaning up any existing processes...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1
timeout /t 1 /nobreak >nul


:: Start Flask server
echo 📡 [1/3] Starting Flask API Server (Port 5000)...
start "🐍 Flask Sync API - Port 5000" /D "%ROOT_DIR%" cmd /k "echo Flask Sync API Server Starting... && cd /d %ROOT_DIR% && python ghl_sync_orders_flask_service.py"

:: Wait for Flask to start
timeout /t 3 /nobreak >nul

:: Start Next.js server  
echo 🌐 [2/3] Starting Next.js Frontend (Port 3000)...
start "⚛️ Next.js Frontend - Port 3000" /D "%NEXTJS_DIR%" cmd /k "echo Next.js Frontend Starting... && npm run dev"

:: Wait for Next.js to start
timeout /t 3 /nobreak >nul

:: Start WhatsApp backend service
echo 💬 [3/3] Starting WhatsApp Backend Service (Port 3001)...
start "💬 WhatsApp Backend - Port 3001" /D "%WHATSAPP_DIR%" cmd /k "echo WhatsApp Backend Starting... && node server.js"

echo.

echo ==========================================
echo   ✅ All servers are starting up!
echo ==========================================
echo   🐍 Flask API:      http://localhost:5000
echo   🌐 Next.js App:    http://localhost:3000
echo   💬 WhatsApp API:   http://localhost:3001
echo ==========================================
echo.
echo 💡 The servers are running in separate windows.
echo 💡 Close those windows to stop the servers.
echo.
echo ⏰ This launcher will close in 10 seconds...

:: Countdown
for /l %%i in (10,-1,1) do (
    echo %%i...
    timeout /t 1 /nobreak >nul
)

echo.
echo ✨ Server launcher finished!
echo Happy coding! 🎉