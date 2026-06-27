@echo off
setlocal
cd /d "%~dp0"
if not exist "config.yml" copy "config.example.yml" "config.yml"
echo Config check done.
pause
