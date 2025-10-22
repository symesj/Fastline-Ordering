# Fastline Ordering Server Launcher (PowerShell)
# This script starts both Flask and Next.js servers

param(
    [switch]$WaitForExit = $false
)

# Set console properties
$Host.UI.RawUI.WindowTitle = "Fastline Ordering - Server Launcher"
Clear-Host

Write-Host "========================================" -ForegroundColor Green
Write-Host "   Fastline Ordering Server Launcher" -ForegroundColor Green  
Write-Host "========================================" -ForegroundColor Green
Write-Host

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "Script location: $ScriptDir" -ForegroundColor Cyan

# Set paths
$FlaskDir = Join-Path $ScriptDir "flask_app"
$NextJsDir = Join-Path $ScriptDir "ghl-custom-frontend"

Write-Host "Flask directory: $FlaskDir" -ForegroundColor Yellow
Write-Host "Next.js directory: $NextJsDir" -ForegroundColor Yellow
Write-Host

# Check if directories exist
if (-not (Test-Path $FlaskDir)) {
    Write-Host "ERROR: Flask directory not found: $FlaskDir" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path $NextJsDir)) {
    Write-Host "ERROR: Next.js directory not found: $NextJsDir" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if Node.js is available
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found. Please install Node.js first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host
Write-Host "Starting servers..." -ForegroundColor Yellow
Write-Host

# Start Flask server
Write-Host "[1/2] Starting Flask API server (Port 5000)..." -ForegroundColor Cyan
try {
    $flaskProcess = Start-Process powershell -ArgumentList @(
        "-NoExit", 
        "-Command", 
        "cd '$FlaskDir'; Write-Host 'Flask API Server Starting...' -ForegroundColor Green; python app_orders.py"
    ) -WindowStyle Normal -PassThru
    
    Write-Host "✓ Flask server started (PID: $($flaskProcess.Id))" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to start Flask server: $_" -ForegroundColor Red
}

# Wait a moment
Start-Sleep -Seconds 2

# Start Next.js server
Write-Host "[2/2] Starting Next.js frontend server (Port 3000)..." -ForegroundColor Cyan
try {
    $nextjsProcess = Start-Process powershell -ArgumentList @(
        "-NoExit", 
        "-Command", 
        "cd '$NextJsDir'; Write-Host 'Next.js Frontend Starting...' -ForegroundColor Green; npm run dev"
    ) -WindowStyle Normal -PassThru
    
    Write-Host "✓ Next.js server started (PID: $($nextjsProcess.Id))" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to start Next.js server: $_" -ForegroundColor Red
}

Write-Host
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Both servers are starting up!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Flask API:     http://localhost:5000" -ForegroundColor White
Write-Host "  Next.js App:   http://localhost:3000" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Green
Write-Host
Write-Host "The servers are running in separate windows." -ForegroundColor Yellow
Write-Host "Close those windows to stop the servers." -ForegroundColor Yellow
Write-Host

if ($WaitForExit) {
    Read-Host "Press Enter to exit this launcher"
} else {
    Write-Host "Launcher will close in 5 seconds..." -ForegroundColor Gray
    Start-Sleep -Seconds 5
}