from selenium import webdriver
import time

driver = webdriver.Edge()
driver.maximize_window()
driver.get("https://www.jd.com")
time.sleep(3)

# ===== 第一步：查看 Cookie =====
cookies = driver.get_cookies()
print(f"=" * 40)
print(f"🍪 京东首页共有 {len(cookies)} 个 Cookie")
for i, c in enumerate(cookies[:5], 1):  # 只显示前5个
    print(f"  {i}. {c['name']}: {str(c['value'])[:30]}...")
if len(cookies) > 5:
    print(f"  ... 还有 {len(cookies) - 5} 个")

# ===== 第二步：JS 获取页面信息 =====
page_height = driver.execute_script("return document.body.scrollHeight")
inner_height = driver.execute_script("return window.innerHeight")
print(f"\n📏 页面总高度: {page_height}px")
print(f"📏 窗口可见高度: {inner_height}px")
print(f"📏 需要滚动的次数约: {int(page_height / inner_height)} 次")

# ===== 第三步：滚动到底部 =====
driver.execute_script(
    "window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})"
)
time.sleep(2)
print("\n⬇️ 已平滑滚动到底部！")

# ===== 第四步：截图保存 =====
driver.save_screenshot("jd_scroll_bottom.png")
print("📸 截图已保存为 jd_scroll_bottom.png")

# ===== 回到顶部确认 =====
driver.execute_script("window.scrollTo(0, 0)")
time.sleep(1)
print("⬆️ 回到顶部")

driver.quit()
print("\n✅ 练习完成！")
