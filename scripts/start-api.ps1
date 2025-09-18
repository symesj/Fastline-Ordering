param(
    [string]$Port = "5050",
    [string]$LogLevel = "DEBUG"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$venvPath = Join-Path $repoRoot 'venv'
$activateScript = Join-Path $venvPath 'Scripts/Activate.ps1'

if (-not (Test-Path $activateScript)) {
    throw "Virtual environment not found at $venvPath. Run 'python -m venv venv' first."
}

& $activateScript

$env:PORT = $Port
$env:LOG_LEVEL = $LogLevel

Write-Host "Starting Fastline Orders API on port $Port..."
python (Join-Path $repoRoot 'ghl_sync_orders_flask_service.py')