from selenium import webdriver
from selenium.webdriver.common.by import By
import time

driver = webdriver.Edge()
driver.get("https://www.baidu.com")
time.sleep(2)

#获取所有cookies
cookies = driver.get_cookies()
print(f"当前共有{len(cookies)}个Cookies:")
for c in cookies:
    print(f"-{c['name']}:{c['value'][:20]}...")
#获取单个cookie
baiduid = driver.get_cookie("BAIDUID")
print(f'\nBAIDUID的值:{baiduid}')

#添加自定义cookie
driver.add_cookie({
    "name":"mytest_cookie",
    "value":"hello_selenium",
    "domain":".baidu.com"
})

print("\n已添加自定义Cookie:my_test_cookie")

#删除指定 cookie
driver.delete_cookie("my_test_cookie")
print("已删除my_test_cookie")

# 删除所有cookie(慎用,会退出登入)
#driver.delete_all_cookies()

driver.quit()