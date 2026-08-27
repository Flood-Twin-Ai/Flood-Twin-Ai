@echo off
python -m venv venv
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pytest -q
echo.
echo Setup complete. Run run_windows.bat to start JAL-DRISHTI.
pause
