# -*- coding: utf-8 -*-
"""
Airtest 入门 Demo
Airtest 是网易出品的自动化测试框架，支持图像识别 + UI控件操作
特别适合游戏测试（Unity/Cocos/原生）

安装完成:
  airtest 1.4.3  +  pocoui 1.0.94
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 55)
print("  Airtest 核心概念 (对比 Selenium)")
print("=" * 55)

print("""
+------------------+---------------------------+---------------------------+
|     操作         |      Selenium 写法         |      Airtest 写法          |
+------------------+---------------------------+---------------------------+
| 打开网页/App     | driver.get("url")         | start_app("包名")         |
| 点击元素         | element.click()           | touch(Template("截图"))    |
| 输入文字         | send_keys("xx")           | text("要输入的文字")       |
| 等待元素         | WebDriverWait             | wait(Template("截图"))     |
| 断言验证         | assert "xx" in title      | assert_exists(Template())  |
| 滑动屏幕         | ActionChains(复杂)        | swipe(起点, 终点)          |
| 截图保存         | save_screenshot("f.png")  | snapshot("f.png")          |
+------------------+---------------------------+---------------------------+
""")

print("=" * 55)
print("  Airtest vs Selenium 适用场景对比")
print("=" * 55)

print("""
  Selenium 适合:
    - Web 网页测试 (电商、后台管理系统、H5页面)
    - 需要精确操作 DOM 元素
    - 做接口+UI 联合测试

  Airtest 适合:
    - 游戏测试 (Unity/Cocos/UE 等引擎游戏) [推荐!]
    - 手机 App 测试 (不需要 Appium 那么重的环境)
    - 不需要代码定位, 靠截图就能跑的测试
    - 跨平台 (Android/iOS/Windows/Web 都支持)
""")

print("=" * 55)
print("  恐龙岛项目实战 - Airtest 脚本示例")
print("=" * 55)

print("""
# ===== 恐龙岛 - 自动挂机测试脚本 =====

from airtest.core.api import *
from poco.drivers.unityengine import UnityPoco

# 1. 连接设备
connect_device("Android:///")      # 手机: USB连接
# connect_device("Windows:///")    # 电脑: Windows模式

# 2. 启动游戏
start_app("com.dinosaur.game")
sleep(5)

# 3. 用 Poco 读取游戏内UI控件
poco = UnityPoco()                  # Unity引擎用这个

# --- 测试: 进入自动培养池 ---
poco("Btn_CultivatePool").click()   # 点击"培养池"按钮
sleep(2)
assert_exists(Template("cultivate_pool.png"), "培养池界面")

# --- 测试: 选择恐龙 ---
poco(text="霸王龙").click()         # 找到"霸王龙"并点击
poco("Btn_StartCultivate").click()  # 点击"开始培养"
sleep(1)

# --- 测试: 验证培养状态 ---
status = poco("Text_Status").get_text()
print(f"培养状态: {status}")
assert "培养中" in status, "培养未开始!"

# --- 测试: 滑动查看更多恐龙 ---
swipe([500, 1500], [500, 500])      # 向上滑动

# --- 截图保存 ---
snapshot("cultivate_pool_test.png")

# 4. 退出游戏
stop_app("com.dinosaur.game")
""")

print("=" * 55)
print("  学习路线")
print("=" * 55)

print("""
  第1步: 下载 AirtestIDE (可视化编辑器, 强烈推荐)
         https://airtest.netease.com/
         - 边操作边录脚本, 不用写代码
         - 自带设备管理, 截图, Poco Inspector
         - 新手首选

  第2步: 学会图像识别操作
         touch / wait / assert_exists / snapshot

  第3步: 学会 Poco 控件操作
         poco("控件名").click()
         poco(text="文字").get_text()

  第4步: 数据驱动 + pytest 集成
         从 Excel 读测试数据, 批量执行

  第5步: CI/CD 集成
         Jenkins/GitLab CI 自动跑脚本
""")

print("\n环境已就绪: airtest 1.4.3 + pocoui 1.0.94")
print("建议下一步: 下载 AirtestIDE 开始可视化操作")
