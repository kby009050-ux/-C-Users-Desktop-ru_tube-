@echo off
title ru_tube Studio
cd /d "%~dp0"
echo Starting ru_tube Studio...
"venv\Scripts\python.exe" app.py
if errorlevel 1 (
    echo.
    echo Server stopped with error.
    pause
)
pause
