# nlsh Windows Installation Script
# Run: irm https://raw.githubusercontent.com/junaid-mahmood/nlsh/main/install.ps1 | iex

$ErrorActionPreference = "Stop"

$InstallDir = "$env:LOCALAPPDATA\nlsh"
$RepoUrl = "https://github.com/junaid-mahmood/nlsh.git"

Write-Host "Installing nlsh..." -ForegroundColor Cyan

# Check for Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $python) {
    Write-Host "Python 3 is required. Please install it from https://python.org" -ForegroundColor Red
    exit 1
}

$pythonCmd = $python.Source
Write-Host "Found Python at: $pythonCmd" -ForegroundColor Green

# Check for Git
$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) {
    Write-Host "Git is required. Please install it from https://git-scm.com" -ForegroundColor Red
    exit 1
}

# Clone or update repository
if (Test-Path $InstallDir) {
    Write-Host "Updating existing installation..."
    Push-Location $InstallDir
    git pull --quiet
    Pop-Location
} else {
    Write-Host "Downloading nlsh..."
    git clone --quiet $RepoUrl $InstallDir
}

Push-Location $InstallDir

# Create virtual environment
Write-Host "Setting up Python environment..."
& $pythonCmd -m venv venv
& "$InstallDir\venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
& "$InstallDir\venv\Scripts\pip.exe" install --quiet -r requirements.txt

# Create batch file launcher
$batchContent = @"
@echo off
"%LOCALAPPDATA%\nlsh\venv\Scripts\python.exe" "%LOCALAPPDATA%\nlsh\nlsh.py" %*
"@
Set-Content -Path "$InstallDir\nlsh.bat" -Value $batchContent

# Create PowerShell launcher
$ps1Content = @"
& "`$env:LOCALAPPDATA\nlsh\venv\Scripts\python.exe" "`$env:LOCALAPPDATA\nlsh\nlsh.py" @args
"@
Set-Content -Path "$InstallDir\nlsh.ps1" -Value $ps1Content

Pop-Location

# Add to PATH
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$InstallDir*") {
    Write-Host "Adding nlsh to PATH..."
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$InstallDir", "User")
    $env:Path = "$env:Path;$InstallDir"
}

Write-Host ""
Write-Host "nlsh installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "To use nlsh:" -ForegroundColor Yellow
Write-Host "  1. Open a new terminal (to refresh PATH)"
Write-Host "  2. Type 'nlsh' to start"
Write-Host ""
Write-Host "Or start now by running:" -ForegroundColor Yellow
Write-Host "  & '$InstallDir\nlsh.bat'"
Write-Host ""

# Ask if user wants to start now
$start = Read-Host "Start nlsh now? [Y/n]"
if ($start -ne "n" -and $start -ne "N") {
    & "$InstallDir\nlsh.bat"
}
