# start_flask_waitress.ps1
# Launches your Flask app via Waitress from the correct venv and working directory
# Logs stdout to .\logs\waitress.out.log and stderr to .\logs\waitress.err.log

param(
  [int]$Port = 5000
)

$ErrorActionPreference = "Stop"

# --- Resolve project root to the script's directory ---
$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) { $ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path }

# --- Paths ---
$VenvDir       = Join-Path $ProjectRoot "venv"
$WaitressExe   = Join-Path $VenvDir "Scripts\waitress-serve.exe"
$LogDir        = Join-Path $ProjectRoot "logs"
$LogOut        = Join-Path $LogDir "waitress.out.log"
$LogErr        = Join-Path $LogDir "waitress.err.log"

# --- Ensure everything exists ---
if (!(Test-Path $WaitressExe)) {
  throw "Waitress not found at $WaitressExe. Activate venv and `pip install waitress`."
}
if (!(Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }

# --- Optional: open firewall for the chosen port (idempotent) ---
Try {
  if (-not (Get-NetFirewallRule -DisplayName "Fastline Flask Port $Port" -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName "Fastline Flask Port $Port" -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port | Out-Null
  }
} Catch { Write-Warning "Could not create firewall rule: $($_.Exception.Message)" }

# --- Rotate old logs (keep last 5) ---
function Rotate-Log($path) {
  if (Test-Path $path) {
    for ($i = 5; $i -ge 1; $i--) {
      $src = "$path.$i"
      $dst = "$path." + ($i + 1)
      if (Test-Path $src) { Move-Item $src $dst -Force }
    }
    Move-Item $path "$path.1" -Force
  }
}
Rotate-Log $LogOut
Rotate-Log $LogErr

# --- Start the server (background, log to separate files) ---
Push-Location $ProjectRoot
try {
  $proc = Start-Process -FilePath $WaitressExe `
    -ArgumentList @("--listen=0.0.0.0:$Port","app:app") `
    -WorkingDirectory $ProjectRoot `
    -NoNewWindow `
    -RedirectStandardOutput $LogOut `
    -RedirectStandardError  $LogErr `
    -PassThru

  "Started waitress-serve (PID $($proc.Id)) on port $Port."
  "Stdout: $LogOut"
  "Stderr: $LogErr"
} finally {
  Pop-Location
}
