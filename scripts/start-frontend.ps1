param(
    [string]$Port = "3000"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
Push-Location $repoRoot
try {
    $frontendPath = Join-Path $repoRoot 'ghl-custom-frontend'
    Set-Location $frontendPath
    $env:PORT = $Port
    Write-Host "Starting Fastline Next.js frontend on port $Port..."
    npm run start -- --port $Port
}
finally {
    Pop-Location
}