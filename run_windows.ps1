Set-Location -Path $PSScriptRoot
Write-Host "Running SEO Article Analyzer v4.1..."

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "ERROR: .venv was not found. Run install_windows.ps1 first."
    Read-Host "Press Enter to exit"
    exit 1
}

.\.venv\Scripts\python.exe main.py --config config.yml

Write-Host ""
Read-Host "Press Enter to exit"
