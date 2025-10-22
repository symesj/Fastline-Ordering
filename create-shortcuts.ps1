# Create a Desktop Shortcut for Server Launcher
$WshShell = New-Object -comObject WScript.Shell

# Create shortcut on desktop
$DesktopPath = [System.Environment]::GetFolderPath('Desktop')
$ShortcutPath = Join-Path $DesktopPath "Fastline Ordering Servers.lnk"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$PSScriptRoot\start-servers.ps1`""
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.Description = "Start Fastline Ordering Servers"
$Shortcut.WindowStyle = 1
$Shortcut.IconLocation = "shell32.dll,25"  # Server icon
$Shortcut.Save()

Write-Host "✓ Desktop shortcut created: $ShortcutPath" -ForegroundColor Green

# Also create one in the project folder
$ProjectShortcut = Join-Path $PSScriptRoot "🚀 Start Servers.lnk"
$Shortcut2 = $WshShell.CreateShortcut($ProjectShortcut)
$Shortcut2.TargetPath = "powershell.exe"  
$Shortcut2.Arguments = "-ExecutionPolicy Bypass -File `"$PSScriptRoot\start-servers.ps1`""
$Shortcut2.WorkingDirectory = $PSScriptRoot
$Shortcut2.Description = "Start Fastline Ordering Servers"
$Shortcut2.WindowStyle = 1
$Shortcut2.IconLocation = "shell32.dll,25"
$Shortcut2.Save()

Write-Host "✓ Project shortcut created: $ProjectShortcut" -ForegroundColor Green

Write-Host
Write-Host "You can now double-click either shortcut to start the servers!" -ForegroundColor Yellow