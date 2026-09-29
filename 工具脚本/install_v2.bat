@echo off
echo 微信自动回复系统 v2.0 安装程序
echo ========================================
echo 基于 itchat-uos（微信网页版API）
echo 无需微信窗口在前台，更稳定！
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python未安装！
    echo 请先安装Python 3.8或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [信息] Python已安装
python --version

echo.
echo [步骤1] 安装itchat-uos依赖
echo 正在安装itchat-uos...
pip install itchat-uos==1.5.0.dev0

if errorlevel 1 (
    echo [警告] itchat-uos安装失败，尝试其他版本...
    pip install itchat-uos
)

if errorlevel 1 (
    echo [警告] 仍然失败，尝试安装普通itchat...
    pip install itchat
)

if errorlevel 1 (
    echo [错误] 所有itchat版本安装失败！
    echo 请手动安装:
    echo pip install itchat-uos==1.5.0.dev0
    echo 或访问: https://github.com/why2lyj/ItChat-UOS
    pause
    exit /b 1
)

echo [成功] itchat安装完成

echo.
echo [步骤2] 检查依赖
pip show itchat-uos || pip show itchat

echo.
echo [步骤3] 安装额外依赖
echo 正在安装requests用于更好的网络支持...
pip install requests

echo.
echo [步骤4] 创建快速启动脚本
echo @echo off > start_wechat_v2.bat
echo echo 微信自动回复系统 v2.0 >> start_wechat_v2.bat
echo echo ======================================== >> start_wechat_v2.bat
echo echo 基于微信网页版API >> start_wechat_v2.bat
echo echo 无需微信窗口在前台 >> start_wechat_v2.bat
echo echo 按Ctrl+C可以停止程序 >> start_wechat_v2.bat
echo echo. >> start_wechat_v2.bat
echo cd /d "%~dp0" >> start_wechat_v2.bat
echo python wechat_auto_reply_v2.py >> start_wechat_v2.bat
echo pause >> start_wechat_v2.bat

echo [成功] 快速启动脚本已创建

echo.
echo [步骤5] 使用说明
echo.
echo 【使用方法】:
echo 1. 运行 start_wechat_v2.bat
echo 2. 使用手机微信扫描二维码登录
echo 3. 系统会自动监控并回复消息
echo.
echo 【重要提醒】:
echo 1. 需要手机微信扫码登录网页版
echo 2. 二维码会在命令行显示（可能需要调整命令行窗口大小）
echo 3. 如果二维码显示异常，尝试：
echo    - 调整命令行窗口大小
echo    - 使用其他终端（如Windows Terminal）
echo    - 修改配置文件中的 enable_cmd_qr: false
echo 4. 首次登录后，下次启动可能无需扫码
echo.
echo 【配置说明】:
echo 1. 编辑 wechat_config_v2.json 修改回复规则
echo 2. 可以设置工作时间、回复对象等
echo 3. 消息历史保存在 wechat_history_v2.json
echo.
echo [安装完成！]
echo.
echo 现在可以:
echo 1. 直接双击 start_wechat_v2.bat 启动
echo 2. 或运行: python wechat_auto_reply_v2.py
echo.
pause