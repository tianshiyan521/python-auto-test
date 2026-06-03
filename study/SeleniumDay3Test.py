from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#1.创建浏览器驱动(这一步不能少!)
service = Service("C:/Users/Administrator/WorkBuddy/Claw/msedgedriver.exe")
driver = webdriver.Edge(service=service)

#2.打开页面
driver.get("https://www.baidu.com")

#3.显示等待
wait = WebDriverWait(driver,timeout=15,poll_frequency=0.5)

su_button = wait.until(
    EC.element_to_be_clickable((By.ID,"chat-submit-button"))
)

su_button.click()
input("请回车")
driver.quit()