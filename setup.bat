@echo off
setlocal
cd /d "%~dp0"
py -3 -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (echo Setup failed.&pause&exit /b 1)
echo Setup complete.
pause
