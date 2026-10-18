@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-windows.ps1"
set "result=%errorlevel%"
if not "%result%"=="0" echo Windows setup failed. See the error above.
if "%~1"=="" pause
exit /b %result%
