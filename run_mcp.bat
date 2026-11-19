@echo off
setlocal
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
  echo ru_tube virtual environment not found.
  echo Run: py -3.12 -m venv venv
  echo Then: venv\Scripts\python.exe -m pip install -r requirements.txt
  pause
  exit /b 1
)
"venv\Scripts\python.exe" mcp_server.py
if errorlevel 1 pause
