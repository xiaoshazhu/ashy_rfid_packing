@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
title WDIP RS485 Serial Profile Read-Only Probe
cd /d "%~dp0"

echo ===================================================
echo       WDIP RS485 Serial Profile Read-Only Probe
echo ===================================================
echo [INFO] Close the packing scanner and vendor software first.
echo [INFO] This probe only reads and never writes WDIP registers.
echo.

set "APP_PYTHON=C:\Users\Admin\AppData\Local\Programs\Python\Python310\python.exe"
if not exist "%APP_PYTHON%" set "APP_PYTHON="
if not defined APP_PYTHON for /f "delims=" %%P in ('where python.exe 2^>nul') do if not defined APP_PYTHON set "APP_PYTHON=%%P"

if not defined APP_PYTHON (
    echo [ERROR] Python was not found.
    pause
    exit /b 1
)

"%APP_PYTHON%" "%~dp0wdip_serial_profile_probe.py"
set "EXIT_CODE=%ERRORLEVEL%"
echo.
echo [INFO] Exit code: %EXIT_CODE%
echo Copy all console output back to Codex.
pause
endlocal & exit /b %EXIT_CODE%
