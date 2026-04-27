@echo off
echo Starting SightSync AI Face Recognition Attendance System...
echo ==============================================

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting the Flask Application...
echo Please open http://127.0.0.1:5000 in your browser.
echo ==============================================
python app.py

pause
