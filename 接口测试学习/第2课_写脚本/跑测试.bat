@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PYEXE="
if not defined PYEXE if exist "C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe" call :check "C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
if not defined PYEXE if exist "C:\Study\python.exe" call :check "C:\Study\python.exe"
if not defined PYEXE set "PYEXE=python"

echo   [Python] %PYEXE%
echo.

"%PYEXE%" run_tests.py

echo.
echo   ---- Done. Press any key to close this window ----
pause >nul
exit /b

:check
"%~1" -c "import requests" >nul 2>&1
if not errorlevel 1 set "PYEXE=%~1"
exit /b
