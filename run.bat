@echo off
chcp 65001 > nul
title ru_tube Launcher

echo ======================================================
echo           ▶ ru_tube 유튜브 & 음악 다운로더 ◀
echo ======================================================
echo.

cd /d "%~dp0"

if exist "venv\Scripts\python.exe" (
    echo [1/2] 가상환경 활성화 완료!
    echo [2/2] 웹 브라우저 및 서버를 시작합니다...
    start http://127.0.0.1:5000
    "venv\Scripts\python.exe" app.py
) else (
    echo [오류] 가상환경을 찾을 수 없습니다.
    pause
)

pause
