@echo off
setlocal
cd /d "%~dp0"
echo Installing SEO Article Analyzer v6.2.2...

if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if not exist ".venv\Scripts\python.exe" python -m venv .venv

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Python venv was not created.
    echo Try running these commands manually in PowerShell.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt

if not exist "config.yml" copy "config.example.yml" "config.yml"

echo.
echo Done. Edit config.yml and run run_windows.bat
pause
