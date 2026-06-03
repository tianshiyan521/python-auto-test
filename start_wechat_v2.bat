@echo off 
chcp 65001 >nul 
echo 微信自动回复系统 v2.0 
echo ======================================== 
echo 基于微信网页版API 
echo 无需微信窗口在前台 
echo 按Ctrl+C可以停止程序 
echo. 
cd /d "%~dp0" 
python wechat_auto_reply_v2.py 
pause 
