@echo off
echo =========================================
echo   Baba Nanak Dairy Management System
echo =========================================
echo.

python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python not found!
    echo Install Python from https://python.org
    echo Make sure to check "Add Python to PATH"
    pause & exit /b
)

echo Installing required libraries...
pip install customtkinter reportlab pillow --quiet

echo.
echo Starting application...
python main.py
pause
