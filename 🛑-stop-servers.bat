@echo off
title Fastline Ordering - Server Stopper
color 0C

cls
echo.
echo ==========================================
echo    🛑 Fastline Ordering Server Stopper
echo ==========================================
echo.

echo 🔍 Looking for running servers...
echo.

:: Check for Node.js processes
tasklist /fi "imagename eq node.exe" 2>nul | find /i "node.exe" >nul
if %errorlevel%==0 (
    echo 📱 Found Next.js processes, stopping them...
    taskkill /f /im node.exe >nul 2>&1
    if %errorlevel%==0 (
        echo ✅ Next.js servers stopped
    ) else (
        echo ❌ Failed to stop some Next.js processes
    )
) else (
    echo ℹ️  No Next.js processes found
)

:: Check for Python processes
tasklist /fi "imagename eq python.exe" 2>nul | find /i "python.exe" >nul
if %errorlevel%==0 (
    echo 🐍 Found Python processes, stopping them...
    taskkill /f /im python.exe >nul 2>&1
    if %errorlevel%==0 (
        echo ✅ Python/Flask servers stopped
    ) else (
        echo ❌ Failed to stop some Python processes
    )
) else (
    echo ℹ️  No Python processes found
)

echo.
echo ==========================================
echo   🛑 Server shutdown complete!
echo ==========================================
echo.
echo 💡 All Fastline Ordering servers have been stopped.
echo.
pause