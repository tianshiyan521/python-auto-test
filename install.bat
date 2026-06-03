@echo off
echo 微信自动回复系统安装程序
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
echo [步骤1] 安装wxauto依赖
echo 正在安装wxauto v4...
pip install wxauto==4.0.0

if errorlevel 1 (
    echo [错误] wxauto安装失败！
    echo 请尝试: pip install wxauto==4.0.0 --user
    pause
    exit /b 1
)

echo [成功] wxauto安装完成

echo.
echo [步骤2] 检查依赖
pip show wxauto

echo.
echo [步骤3] 准备运行环境
echo 请确保:
echo 1. 微信客户端已登录
echo 2. 微信窗口在前台可见（不要最小化）
echo 3. 微信窗口大小合适（建议正常窗口大小）

echo.
echo [步骤4] 运行系统
echo 打开一个新的命令行窗口，运行:
echo python wechat_auto_reply.py
echo.
echo 或者直接双击运行 start_wechat_reply.bat
echo.
echo [提示] 按任意键创建启动脚本...
pause >nul

REM 创建启动脚本
echo @echo off > start_wechat_reply.bat
echo echo 微信自动回复系统 >> start_wechat_reply.bat
echo echo ======================================== >> start_wechat_reply.bat
echo echo 请确保微信已登录且窗口在前台 >> start_wechat_reply.bat
echo echo 按Ctrl+C可以停止程序 >> start_wechat_reply.bat
echo echo. >> start_wechat_reply.bat
echo python wechat_auto_reply.py >> start_wechat_reply.bat
echo pause >> start_wechat_reply.bat

echo [成功] 安装完成！
echo.
echo 使用方法:
echo 1. 登录微信并保持窗口在前台
echo 2. 运行 start_wechat_reply.bat
echo 3. 系统会自动回复消息
echo.
echo 配置文件: wechat_config.json
echo 消息历史: wechat_history.json
echo.
pause