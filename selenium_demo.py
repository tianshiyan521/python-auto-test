from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
import time

# 手动指定现有驱动路径（忽略版本警告）
service = Service(executable_path="c:/Users/Administrator/WorkBuddy/Claw/msedgedriver.exe")
options = Options()
# options.add_argument("--headless")  # 先不用无头模式，看实际错误

driver = webdriver.Edge(service=service, options=options)
driver.get("https://www.saucedemo.com")
UserName = driver.find_element(By.ID,"user-name")
PassWord = driver.find_element(By.ID,"password")
Login = driver.find_element(By.ID,"login-button")
time.sleep(1)
UserName.clear()
UserName.send_keys("standard_user")
PassWord.clear()
PassWord.send_keys("secret_sauce")
Login.click()
time.sleep(2)
print("登入后标题",driver.title)
driver.quit()
