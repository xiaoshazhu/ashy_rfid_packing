@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
title WDIP24-15-R Light Control Test
cd /d "%~dp0"

echo ===================================================
echo          WDIP24-15-R Light Control Test
echo ===================================================
echo [INFO] Close the packing scanner and vendor software first.
echo [INFO] This test uses existing voltage/current settings only.
echo [INFO] It never changes current or saves device parameters.
echo.

set "APP_PYTHON=C:\Users\Admin\AppData\Local\Programs\Python\Python310\python.exe"
if not exist "%APP_PYTHON%" set "APP_PYTHON="
if not defined APP_PYTHON if defined PROJECT_PYTHON if exist "%PROJECT_PYTHON%" set "APP_PYTHON=%PROJECT_PYTHON%"
if not defined APP_PYTHON for /f "delims=" %%P in ('where python.exe 2^>nul') do if not defined APP_PYTHON set "APP_PYTHON=%%P"

if not defined APP_PYTHON (
    echo [ERROR] Python was not found.
    pause
    exit /b 1
)

"%APP_PYTHON%" -c "import serial" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was found, but pyserial is unavailable: %APP_PYTHON%
    pause
    exit /b 1
)

echo [INFO] Python: %APP_PYTHON%
echo.
"%APP_PYTHON%" "%~dp0wdip_light_control_test.py" --port COM3
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo ===================================================
echo [INFO] Exit code: %EXIT_CODE%
echo ===================================================
echo Press any key to close this window...
pause >nul
endlocal & exit /b %EXIT_CODE%
