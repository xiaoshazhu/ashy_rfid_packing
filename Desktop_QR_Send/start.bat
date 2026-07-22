@echo off
setlocal EnableExtensions DisableDelayedExpansion
title Laser Packing Scanner Launcher

cd /d "%~dp0"
if not exist "logs" mkdir "logs" >nul 2>&1

echo ===================================================
echo          Laser Packing Scanner - Startup
echo ===================================================
echo [INFO] Working directory: %CD%
echo [INFO] Starting with the device computer environment...

set "APP_PYTHON="
set "APP_QT_MODE="
set "LAST_PYTHON="

call :try_python "%PROJECT_PYTHON%"
call :try_python "C:\Users\admin\anaconda3\python.exe"
call :try_python "%~dp0.venv\Scripts\python.exe"
call :try_python "%~dp0venv\Scripts\python.exe"
call :try_python "%CONDA_PREFIX%\python.exe"
call :try_python "%USERPROFILE%\anaconda3\python.exe"
call :try_python "%LOCALAPPDATA%\anaconda3\python.exe"
call :try_python "C:\ProgramData\anaconda3\python.exe"
call :try_python "D:\Anaconda3\python.exe"
call :try_python "D:\anaconda3\python.exe"

for /f "delims=" %%P in ('where python.exe 2^>nul') do call :try_python "%%P"

if defined APP_PYTHON goto :run_source

echo.
echo [ERROR] No device Python could load PySide6.QtWidgets.
echo [INFO] The obsolete dist executable will not be used.
if defined LAST_PYTHON (
    echo [DIAG] The final detailed error follows:
    "%LAST_PYTHON%" "%~dp0runtime_bootstrap.py" --check --qt-mode auto
)
set "EXIT_CODE=1"
goto :finished

:run_source
echo [INFO] Device Python: %APP_PYTHON%
echo [INFO] Qt loading mode: %APP_QT_MODE%
echo [INFO] Runtime check passed. Opening the packing scanner...
echo ===================================================
echo.
"%APP_PYTHON%" "%~dp0runtime_bootstrap.py" --qt-mode "%APP_QT_MODE%"
set "EXIT_CODE=%ERRORLEVEL%"
goto :finished

:try_python
if defined APP_PYTHON exit /b 0
set "CANDIDATE=%~1"
if not defined CANDIDATE exit /b 0
if not exist "%CANDIDATE%" exit /b 0
set "LAST_PYTHON=%CANDIDATE%"
call :try_mode "%CANDIDATE%" conda
call :try_mode "%CANDIDATE%" pyside
call :try_mode "%CANDIDATE%" system
exit /b 0

:try_mode
if defined APP_PYTHON exit /b 0
"%~1" "%~dp0runtime_bootstrap.py" --check --quiet --qt-mode "%~2"
if errorlevel 1 exit /b 0
set "APP_PYTHON=%~1"
set "APP_QT_MODE=%~2"
exit /b 0

:finished
if not defined EXIT_CODE set "EXIT_CODE=1"
echo.
echo ===================================================
if "%EXIT_CODE%"=="0" (
    echo [INFO] The packing scanner closed normally.
) else (
    echo [ERROR] The packing scanner did not start. Exit code: %EXIT_CODE%
    echo [INFO] Details were saved to logs\startup.log.
)
echo ===================================================
echo.
echo Press any key to close this window...
pause >nul
endlocal & exit /b %EXIT_CODE%
