Set-Location -Path $PSScriptRoot
Write-Host "Installing SEO Article Analyzer v4.1..."

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    py -3 -m venv .venv
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    python -m venv .venv
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "ERROR: Python venv was not created."
    Read-Host "Press Enter to exit"
    exit 1
}

.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

if (-not (Test-Path "config.yml")) {
    Copy-Item "config.example.yml" "config.yml"
}

Write-Host ""
Write-Host "Done. Edit config.yml and run run_windows.bat or run_windows.ps1"
Read-Host "Press Enter to exit"
