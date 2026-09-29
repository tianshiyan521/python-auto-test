@echo off
chcp 65001 >nul
title 接口测试练习台 · 第1课
cd /d "%~dp0"

set "PYEXE=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
if not exist "%PYEXE%" set "PYEXE=python"

echo.
echo   正在启动练习台，浏览器会自动弹出来...
echo.

"%PYEXE%" server.py

echo.
echo   服务已停止。按任意键关闭这个窗口。
pause >nul
