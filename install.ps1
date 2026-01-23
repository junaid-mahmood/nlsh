$InstallDir = Join-Path $HOME ".nlsh"
$RepoUrl = "https://github.com/junaid-mahmood/nlsh.git"

Write-Host "Installing nlsh..." -ForegroundColor Cyan

# Python check
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python is required. Please install it from python.org or the Microsoft Store." -ForegroundColor Red
    exit 1
}

# Update
if (Test-Path $InstallDir) {
    Write-Host "Updating existing installation..."
    pushd $InstallDir
    git pull --quiet
    popd
}
else {
    Write-Host "Downloading nlsh..."
    git clone --quiet $RepoUrl $InstallDir
}

# Setup Python environment
pushd $InstallDir
Write-Host "Setting up Python environment..."
python -m venv venv
& .\venv\Scripts\python.exe -m pip install --quiet --upgrade pip
& .\venv\Scripts\python.exe -m pip install --quiet -r requirements.txt
popd

$BinDir = Join-Path $InstallDir "bin"
if (!(Test-Path $BinDir)) { New-Item -ItemType Directory -Path $BinDir | Out-Null }

$WrapperContent = @"
@echo off
setlocal
call "$InstallDir\venv\Scripts\activate.bat"
python "$InstallDir\nlsh.py" %*
endlocal
"@

Set-Content -Path (Join-Path $BinDir "nlsh.cmd") -Value $WrapperContent

# Add to PATH at user level
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$BinDir*") {
    Write-Host "Adding nlsh to User PATH..."
    $NewPath = "$UserPath;$BinDir"
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    $env:Path = "$env:Path;$BinDir"
}

Write-Host "`nnlsh installed successfully!" -ForegroundColor Green
Write-Host "You may need to restart your terminal for PATH changes to take effect."
Write-Host "Or just run: nlsh"

# PR by DataBoySu