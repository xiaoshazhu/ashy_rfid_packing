@echo off
title Clear Unuploaded Records

echo ===================================================
echo   Clearing local unuploaded test records...
echo ===================================================

set "DEV_PYTHON=C:\Users\Admin\AppData\Local\Programs\Python\Python310\python.exe"

if exist "%DEV_PYTHON%" (
    echo [INFO] Running with device Python environment...
    "%DEV_PYTHON%" "%~dp0reset_local_db.py"
) else (
    echo [INFO] Running with system Python environment...
    python "%~dp0reset_local_db.py"
)

echo.
echo ===================================================
echo   Finished! Please restart the scanner app.
echo ===================================================
pause
