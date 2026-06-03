
"""
新版百度搜索设置自动化脚本
适配2025+新版百度首页
功能：自动打开百度高级设置页面，修改每页显示条数为50条
"""
import os
import struct

# 修复SeleniumManager无法识别架构的问题
if not os.environ.get('PROCESSOR_ARCHITECTURE'):
    arch = 'AMD64' if struct.calcsize('P') * 8 == 64 else 'x86'
    os.environ['PROCESSOR_ARCHITECTURE'] = arch

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.edge.options import Options as EdgeOptions
import time

# 配置Edge浏览器
options = EdgeOptions()
options.binary_location = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
# 可选：无头模式（不显示浏览器窗口）
# options.add_argument("--headless")
# options.add_argument("--disable-gpu")

driver = webdriver.Edge(options=options)
driver.maximize_window()

try:
    # 直接访问百度高级设置页面（新版首页设置入口已改版）
    print("打开百度搜索设置页面...")
    driver.get("https://www.baidu.com/gaoji/preferences.html")
    driver.implicitly_wait(5)
    time.sleep(2)
    
    # 截图查看页面
    driver.save_screenshot("baidu_pref.png")
    
    # 定位每页显示条数下拉框
    print("修改每页显示条数...")
    nr_select = driver.find_element(By.NAME, "NR")
    select = Select(nr_select)
    
    # 获取当前选中值
    current_value = select.first_selected_option.get_attribute("value")
    print(f"当前每页显示: {current_value} 条")
    
    # 选择50条
    select.select_by_value("50")
    print("已选择每页显示50条")
    
    # 点击保存设置按钮
    print("保存设置...")
    save_btn = driver.find_element(By.CSS_SELECTOR, "input[value='保存设置']")
    save_btn.click()
    
    time.sleep(1)
    
    # 处理确认弹窗
    try:
        alert = driver.switch_to.alert
        alert_text = alert.text
        print(f"弹窗提示: {alert_text}")
        alert.accept()
        print("已确认保存")
    except Exception as e:
        print(f"没有弹窗或处理弹窗失败: {e}")
    
    print("✅ 设置已成功保存！")
    
    # 验证设置是否生效
    time.sleep(2)
    driver.get("https://www.baidu.com")
    time.sleep(2)
    driver.save_screenshot("baidu_after_setting.png")
    print("已截图验证设置效果")
    
except Exception as e:
    print(f"❌ 操作失败: {e}")
    driver.save_screenshot("error.png")
    
finally:
    time.sleep(2)
    driver.quit()
    print("浏览器已关闭")
