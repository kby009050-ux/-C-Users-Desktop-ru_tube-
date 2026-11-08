@echo off
chcp 65001 > nul
title ru_tube Launcher

echo ======================================================
echo           ▶ ru_tube 유튜브 & 음악 다운로더 ◀
echo ======================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [경고] Python이 설치되어 있지 않습니다.
    echo 파이썬 공식 사이트(https://www.python.org)에서 Python 3을 설치해 주세요.
    pause
    exit /b
)

if not exist venv (
    echo [1/3] 가상환경(venv)을 생성하는 중입니다...
    python -m venv venv
)

echo [2/3] 필요한 패키지를 점검 및 설치하는 중입니다...
call venv\Scripts\activate.bat
pip install -r requirements.txt --quiet

echo [3/3] ru_tube 웹 서버를 시작합니다...
start http://127.0.0.1:5000
python app.py

pause
