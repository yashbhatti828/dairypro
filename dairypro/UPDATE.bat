@echo off
title Baba Nanak Dairy — Updater
color 0A
echo.
echo  =========================================
echo    Baba Nanak Dairy — Software Updater
echo  =========================================
echo.
echo  Checking Python...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo  [ERROR] Python not found. Install from python.org
    pause & exit /b
)
echo  Running updater...
echo.
python updater.py
echo.
pause
