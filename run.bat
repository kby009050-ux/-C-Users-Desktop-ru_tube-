@echo off
title ru_tube
cd /d "%~dp0"
echo ====================================
echo Starting ru_tube Web Server...
echo ====================================
echo.
start http://127.0.0.1:5000
"venv\Scripts\python.exe" app.py
if errorlevel 1 (
    echo.
    echo An error occurred while running the server.
    pause
)
