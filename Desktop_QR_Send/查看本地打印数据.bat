@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python310\python.exe"
if exist "%PYTHON_EXE%" goto run_probe

for /f "delims=" %%P in ('where python 2^>nul') do (
    set "PYTHON_EXE=%%P"
    goto run_probe
)

echo [ERROR] 未找到Python 3.10，请先确认start.bat可以正常运行。
pause
exit /b 1

:run_probe
"%PYTHON_EXE%" "%~dp0view_local_test_data.py"
echo.
pause
