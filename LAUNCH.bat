@echo off
title Nexus Defense v2 - Launcher
color 0B
echo.
echo  ============================================
echo   NEXUS DEFENSE v2 - Starting...
echo  ============================================
echo.
cd /d "%~dp0"
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found! Install from https://python.org
    pause & exit
)
echo  Checking dependencies...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo  Installing Flask...
    pip install flask
)
echo.
echo  Server: http://localhost:5000
echo  Ctrl+C to stop.
echo.
python server.py
pause
