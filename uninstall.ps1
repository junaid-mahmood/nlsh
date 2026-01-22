# nlsh Windows Uninstallation Script

$ErrorActionPreference = "Stop"

$InstallDir = "$env:LOCALAPPDATA\nlsh"

Write-Host "Uninstalling nlsh..." -ForegroundColor Cyan

# Remove installation directory
if (Test-Path $InstallDir) {
    Remove-Item -Recurse -Force $InstallDir
    Write-Host "Removed installation directory" -ForegroundColor Green
} else {
    Write-Host "Installation directory not found" -ForegroundColor Yellow
}

# Remove from PATH
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -like "*$InstallDir*") {
    $newPath = ($userPath -split ";" | Where-Object { $_ -ne $InstallDir }) -join ";"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "Removed nlsh from PATH" -ForegroundColor Green
}

Write-Host ""
Write-Host "nlsh has been uninstalled." -ForegroundColor Green
Write-Host "Note: Open a new terminal for PATH changes to take effect." -ForegroundColor Yellow
