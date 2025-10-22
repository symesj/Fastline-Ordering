# Stop Fastline Ordering Servers
param(
    [switch]$Force = $false
)

Clear-Host
Write-Host "========================================" -ForegroundColor Red
Write-Host "   Stopping Fastline Ordering Servers" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host

# Find and stop Node.js processes (Next.js)
$nodeProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue
if ($nodeProcesses) {
    Write-Host "Found $($nodeProcesses.Count) Node.js process(es)..." -ForegroundColor Yellow
    foreach ($proc in $nodeProcesses) {
        try {
            if ($Force) {
                $proc | Stop-Process -Force
                Write-Host "✓ Forcefully stopped Node.js process (PID: $($proc.Id))" -ForegroundColor Red
            } else {
                $proc | Stop-Process
                Write-Host "✓ Stopped Node.js process (PID: $($proc.Id))" -ForegroundColor Green
            }
        } catch {
            Write-Host "✗ Could not stop Node.js process (PID: $($proc.Id)): $_" -ForegroundColor Red
        }
    }
} else {
    Write-Host "No Node.js processes found." -ForegroundColor Gray
}

# Find and stop Python processes (Flask)
$pythonProcesses = Get-Process -Name "python*" -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    Write-Host "Found $($pythonProcesses.Count) Python process(es)..." -ForegroundColor Yellow
    foreach ($proc in $pythonProcesses) {
        try {
            if ($Force) {
                $proc | Stop-Process -Force
                Write-Host "✓ Forcefully stopped Python process (PID: $($proc.Id))" -ForegroundColor Red
            } else {
                $proc | Stop-Process
                Write-Host "✓ Stopped Python process (PID: $($proc.Id))" -ForegroundColor Green
            }
        } catch {
            Write-Host "✗ Could not stop Python process (PID: $($proc.Id)): $_" -ForegroundColor Red
        }
    }
} else {
    Write-Host "No Python processes found." -ForegroundColor Gray
}

Write-Host
Write-Host "Server shutdown complete!" -ForegroundColor Green
Write-Host "Use -Force parameter to forcefully kill processes if needed." -ForegroundColor Gray
Write-Host

Read-Host "Press Enter to exit"