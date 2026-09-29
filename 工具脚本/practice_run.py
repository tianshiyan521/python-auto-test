"""
练习脚本 —— 自动搜索 + 截图
跑起来就行，看懂一条注释算一条
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# ====== 第1步：启动浏览器 ======
opt = Options()
opt.add_argument("--start-maximized")

service = Service(executable_path="C:/Users/Administrator/WorkBuddy/Claw/msedgedriver.exe")
driver = webdriver.Edge(service=service, options=opt)
print("浏览器已启动")

try:
    # ====== 第2步：打开 Bing ======
    driver.get("https://www.bing.com")
    print("已打开 Bing")

    # ====== 第3步：等搜索框出现，输入关键词 ======
    wait = WebDriverWait(driver, 10)
    search_box = wait.until(
        EC.element_to_be_clickable((By.NAME, "q"))  # Bing 搜索框的 name 属性是 "q"
    )
    search_box.send_keys("今日科技新闻")
    print("已输入搜索词")

    # ====== 第4步：按回车搜索 ======
    search_box.send_keys(Keys.RETURN)
    print("已执行搜索")

    # ====== 第5步：等搜索结果出来，截个图 ======
    time.sleep(2)
    driver.save_screenshot("bing_result.png")
    print("截图已保存: bing_result.png")

    # ====== 第6步：滚动到底部 ======
    driver.execute_script(
        "window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})"
    )
    print("已滚动到底部")
    time.sleep(2)

    # ====== 第7步：底部截图 ======
    driver.save_screenshot("bing_result_bottom.png")
    print("底部截图已保存: bing_result_bottom.png")

    # ====== 第8步：获取前3条结果 ======
    results = driver.find_elements(By.CSS_SELECTOR, "h2 a")  # Bing 结果链接
    print(f"\n前3条搜索结果：")
    count = 0
    for r in results:
        text = r.text.strip()
        if text:
            count += 1
            print(f"  [{count}] {text}")
        if count >= 3:
            break

    print("\n搞定！看看文件夹里多出来的两张截图。")

finally:
    time.sleep(2)
    driver.quit()
    print("浏览器已关闭")
