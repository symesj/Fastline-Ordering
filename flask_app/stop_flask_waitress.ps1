# stop_flask_waitress.ps1
# Kills any running waitress-serve process from this venv

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir     = Join-Path $ProjectRoot "venv"
$WaitressExe = Join-Path $VenvDir "Scripts\waitress-serve.exe"

$procs = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $WaitressExe }
if ($procs) {
  $count = $procs.Count
  $procs | Stop-Process -Force
  "Stopped {0} instance(s) of waitress-serve." -f $count
} else {
  "No waitress-serve instances found for this app."
}
