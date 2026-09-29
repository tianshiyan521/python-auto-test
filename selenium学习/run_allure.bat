@echo off
chcp 65001 > nul
echo ============================================
echo   必应搜索自动化测试 - Allure 报告
echo ============================================
echo.

echo [1/2] 清理旧报告...
if exist selenium学习/allure-results rmdir /s /q selenium学习/allure-results

echo [2/2] 运行测试 & 打开 Allure 报告...
C:\Study\python.exe -m pytest selenium学习/SeleniumDay10_bing.py -v --alluredir=selenium学习/allure-results

echo.
echo 启动 Allure 本地服务器（端口 8888）...
start http://localhost:8888
allure serve selenium学习/allure-results --port 8888
