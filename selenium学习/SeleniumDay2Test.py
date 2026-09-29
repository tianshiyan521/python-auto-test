from selenium import webdriver
from selenium.webdriver.common.by import By
import time

driver = webdriver.Edge()
driver.get("https://www.saucedemo.com/")

#找到用户名输入框,输入账号
driver.find_element(By.ID,"user-name").send_keys("standard_user")

#找到密码输入框,输入密码
driver.find_element(By.ID,"password").send_keys("secret_sauce")

#点击登入按钮
driver.find_element(By.ID,'login-button').click()

time.sleep(2)

print("登录后标题:",driver.title)
assert "swag" in driver.title.lower(),"登录失败"
print("登入成功")
driver.quit()