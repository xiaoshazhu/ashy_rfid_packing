@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
title RS485 Top Button Channel Probe

cd /d "%~dp0"
if not exist "logs" mkdir "logs" >nul 2>&1

echo ===================================================
echo          RS485 Top Button Channel Probe
echo ===================================================
echo [INFO] Formal program and old button test must be closed.
echo [INFO] Only read-only Modbus commands are sent.
echo [INFO] Camera, printer, server and database are disabled.

set "APP_PYTHON="
call :try_python "%PROJECT_PYTHON%"
call :try_python "C:\Users\admin\anaconda3\python.exe"
call :try_python "%~dp0.venv\Scripts\python.exe"
call :try_python "%CONDA_PREFIX%\python.exe"
call :try_python "%USERPROFILE%\anaconda3\python.exe"
call :try_python "C:\ProgramData\anaconda3\python.exe"
call :try_python "D:\anaconda3\python.exe"
for /f "delims=" %%P in ('where python.exe 2^>nul') do call :try_python "%%P"

if not defined APP_PYTHON (
    echo [ERROR] No Python containing pyserial was found.
    set "EXIT_CODE=1"
    goto :finished
)

echo [INFO] Python: %APP_PYTHON%
echo ===================================================
echo.
"%APP_PYTHON%" "%~dp0rs485_input_probe.py" --port COM3
set "EXIT_CODE=%ERRORLEVEL%"
goto :finished

:try_python
if defined APP_PYTHON exit /b 0
set "CANDIDATE=%~1"
if not defined CANDIDATE exit /b 0
if not exist "%CANDIDATE%" exit /b 0
"%CANDIDATE%" -c "import serial" >nul 2>&1
if errorlevel 1 exit /b 0
set "APP_PYTHON=%CANDIDATE%"
exit /b 0

:finished
echo.
echo ===================================================
if "%EXIT_CODE%"=="0" (
    echo [INFO] Probe closed normally.
) else (
    echo [ERROR] Probe finished with exit code: %EXIT_CODE%
)
echo [INFO] Result: logs\rs485_input_probe.log
echo ===================================================
echo.
echo Press any key to close this window...
pause >nul
endlocal & exit /b %EXIT_CODE%
