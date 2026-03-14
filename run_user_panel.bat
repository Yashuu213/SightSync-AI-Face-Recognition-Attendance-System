@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
echo [DEBUG] Current Directory: %cd%
echo Starting Face Recognition - User Attendance Kiosk...
echo ===================================================

if not exist venv\Scripts\python.exe (
    echo [ERROR] Virtual environment python not found at venv\Scripts\python.exe
    echo Please run run_app.bat first to set up the environment.
    pause
    exit /b 1
)

echo [DEBUG] Found Python at venv\Scripts\python.exe
echo [DEBUG] Version Info:
venv\Scripts\python.exe --version

echo.
echo Opening User Attendance Panel in Browser...
start "" "http://127.0.0.1:5000/user"

echo.
echo Starting the Application Server...
echo Keep this window open while using the kiosk.
echo ===================================================

:: Run python directly and capture any immediate crash
venv\Scripts\python.exe app.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Application crashed with exit code %ERRORLEVEL%
)

echo.
echo Press any key to close this window...
pause >nul
