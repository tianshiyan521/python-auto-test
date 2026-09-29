@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set PYEXE=
if exist "C:\Study\python.exe" set PYEXE=C:\Study\python.exe

if "%PYEXE%"=="" (
    echo.
    echo   [ERROR] Python not found at C:\Study\python.exe
    echo   Please install Python or edit PYEXE in this file.
    echo.
    pause
    exit /b 1
)

echo.
echo   [Python] %PYEXE%
echo.
"%PYEXE%" run_tests.py
set RC=%ERRORLEVEL%

echo.
if "%RC%"=="0" (
    echo   ---- ALL PASSED ----
) else (
    echo   ---- HAS FAILURES, exit code %RC% ----
)
echo.
echo   Press any key to close...
pause >nul
exit /b %RC%
