@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
title T63R Printer Read-Only Status Probe
cd /d "%~dp0"

echo ===================================================
echo       T63R Printer / RFID Read-Only Status Probe
echo ===================================================
echo [INFO] Close the packing scanner and vendor demo first.
echo [SAFE] No printing, no paper feeding, no RFID writing, no database.

set "APP_PYTHON="
call :try_python "%PROJECT_PYTHON%"
call :try_python "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
call :try_python "%~dp0.venv\Scripts\python.exe"
call :try_python "%USERPROFILE%\anaconda3\python.exe"
call :try_python "C:\ProgramData\anaconda3\python.exe"
for /f "delims=" %%P in ('where python.exe 2^>nul') do call :try_python "%%P"

if not defined APP_PYTHON (
    echo [ERROR] No usable Python was found.
    set "EXIT_CODE=1"
    goto :finished
)

echo [INFO] Python: %APP_PYTHON%
"%APP_PYTHON%" "%~dp0t63r_status_probe.py"
set "EXIT_CODE=%ERRORLEVEL%"
goto :finished

:try_python
if defined APP_PYTHON exit /b 0
set "CANDIDATE=%~1"
if not defined CANDIDATE exit /b 0
if not exist "%CANDIDATE%" exit /b 0
"%CANDIDATE%" -c "import ctypes" >nul 2>&1
if errorlevel 1 exit /b 0
set "APP_PYTHON=%CANDIDATE%"
exit /b 0

:finished
echo.
echo ===================================================
echo [INFO] Exit code: %EXIT_CODE%
echo [INFO] Copy all console output back to Codex.
echo ===================================================
pause
endlocal & exit /b %EXIT_CODE%
