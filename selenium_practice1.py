# -*- coding: utf-8 -*-
"""
Selenium 练习1 - pytest 基础 + 元素定位
这是摸鱼学习计划的第一步

学会之后你就知道怎么用 pytest 组织测试用例了
比纯写脚本规范100倍，面试也经常问
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# ============================================
# 知识点1: Selenium 8种元素定位方式
# ============================================

print("=" * 55)
print("  Selenium 8种元素定位方式")
print("=" * 55)

print("""
在网页上操作任何东西之前, 先要"找到"它:

1. By.ID           - 通过元素ID定位 (最常用, 最稳定)
   driver.find_element(By.ID, "username")

2. By.NAME         - 通过name属性定位
   driver.find_element(By.NAME, "q")

3. By.CLASS_NAME   - 通过class名定位 (注意可能有多个)
   driver.find_element(By.CLASS_NAME, "btn")

4. By.TAG_NAME     - 通过标签名定位
   driver.find_element(By.TAG_NAME, "input")

5. By.LINK_TEXT    - 通过链接文字定位 (精准匹配)
   driver.find_element(By.LINK_TEXT, "登录")

6. By.PARTIAL_LINK_TEXT - 通过部分链接文字定位
   driver.find_element(By.PARTIAL_LINK_TEXT, "登")

7. By.CSS_SELECTOR - 通过CSS选择器定位 (最强大)
   driver.find_element(By.CSS_SELECTOR, "#login .btn")
   driver.find_element(By.CSS_SELECTOR, "input[type='text']")

8. By.XPATH        - 通过XPath路径定位 (万能但有坑)
   driver.find_element(By.XPATH, "//input[@id='username']")
   driver.find_element(By.XPATH, "//div[contains(text(),'登录')]")
""")

# ============================================
# 知识点2: find_element vs find_elements
# ============================================

print("=" * 55)
print("  find_element vs find_elements 的区别")
print("=" * 55)

print("""
find_element   - 找第一个匹配的, 找不到就报错
find_elements  - 找所有匹配的, 返回列表, 找不到返回空列表(不报错)

# 只要点第一个, 用这个
btn = driver.find_element(By.ID, "submit")

# 要遍历所有结果, 用这个
items = driver.find_elements(By.CLASS_NAME, "list-item")
for item in items:
    print(item.text)
""")

# ============================================
# 知识点3: 显式等待 (重要!)
# ============================================

print("=" * 55)
print("  等待机制 - 为什么不能用 time.sleep")
print("=" * 55)

print("""
time.sleep(5)  = 笨等5秒, 不管元素有没有出现都要等
WebDriverWait  = 聪明地等, 元素一出现就立刻继续, 最多等X秒

# 推荐写法:
wait = WebDriverWait(driver, 10)  # 最多等10秒

# 等元素出现
element = wait.until(
    EC.presence_of_element_located((By.ID, "username"))
)

# 等元素可点击
button = wait.until(
    EC.element_to_be_clickable((By.ID, "submit"))
)

# 等元素可见
text = wait.until(
    EC.visibility_of_element_located((By.CLASS_NAME, "result"))
)

# 常见等待条件:
# EC.presence_of_element_located   - 元素出现在DOM中
# EC.visibility_of_element_located - 元素可见(显示在页面上)
# EC.element_to_be_clickable       - 元素可点击
# EC.title_contains("xxx")         - 页面标题包含xxx
# EC.url_contains("xxx")           - URL包含xxx
""")

# ============================================
# 实战练习: 用多种方式定位必应搜索框
# ============================================

print("=" * 55)
print("  实战练习 - 用多种方式定位必应搜索框")
print("=" * 55)

options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-automation"])

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 10)

try:
    driver.get("https://www.bing.com")
    print("\n>> 打开必应首页, 用不同方式定位搜索框:\n")

    # 方式1: By.ID
    el1 = wait.until(EC.presence_of_element_located((By.ID, "sb_form_q")))
    print(f"  1. By.ID          -> 成功! 标签: {el1.tag_name}")

    # 方式2: By.NAME
    el2 = driver.find_element(By.NAME, "q")
    print(f"  2. By.NAME        -> 成功! 标签: {el2.tag_name}")

    # 方式3: By.CSS_SELECTOR
    el3 = driver.find_element(By.CSS_SELECTOR, "#sb_form_q")
    print(f"  3. By.CSS_SELECTOR -> 成功! 标签: {el3.tag_name}")

    # 方式4: By.XPATH
    el4 = driver.find_element(By.XPATH, "//input[@id='sb_form_q']")
    print(f"  4. By.XPATH        -> 成功! 标签: {el4.tag_name}")

    # 测试搜索
    el1.send_keys("selenium python")
    el1.send_keys(Keys.ENTER)
    time.sleep(3)

    # 用CSS_SELECTOR提取结果
    results = driver.find_elements(By.CSS_SELECTOR, "h2 a")
    print(f"\n>> 用CSS_SELECTOR提取到 {len(results)} 条搜索结果:")
    for i, r in enumerate(results[:5], 1):
        if r.text.strip():
            print(f"  {i}. {r.text.strip()}")

    # 用XPATH提取结果 (对比一下)
    results2 = driver.find_elements(By.XPATH, "//li[contains(@class,'b_algo')]//h2")
    print(f"\n>> 用XPATH提取到 {len(results2)} 条搜索结果:")
    for i, r in enumerate(results2[:5], 1):
        if r.text.strip():
            print(f"  {i}. {r.text.strip()}")

    driver.save_screenshot("selenium_practice1.png")
    print(f"\n>> 截图保存: selenium_practice1.png")
    print(">> [PASS] 练习完成!")

except Exception as e:
    print(f">> [ERROR] {e}")
    driver.save_screenshot("error_practice1.png")

finally:
    driver.quit()

print("\n" + "=" * 55)
print("  本节要点")
print("=" * 55)
print("""
记住:
  - 优先用 By.ID 和 By.CSS_SELECTOR (快且稳定)
  - XPath 是万能的但写起来麻烦, CSS选择器够用就行
  - 永远用 WebDriverWait, 不要 time.sleep
  - find_element 找不到会报错, find_elements 找不到返回空列表
""")
