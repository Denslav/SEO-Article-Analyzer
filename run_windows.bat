@echo off
setlocal
cd /d "%~dp0"
echo Running SEO Article Analyzer v6.2.2...

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: .venv was not found. Run install_windows.bat first.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" main.py --config config.yml
echo.
pause
