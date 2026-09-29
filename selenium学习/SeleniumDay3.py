#import time
#time.sleep(3)#强制等3秒,不管元素是否加载完成
#隐式等待


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service

service = Service("C:/Users/Administrator/WorkBuddy/Claw/msedgedriver.exe")
driver = webdriver.Edge(service=service)
"""
#设置全局隐式等待:整个driver生命周期内都生效
driver.implicitly_wait(10) #最多等10秒,超时抛NoSuchElementException

driver.get("https://www.baidu.com")
driver.find_element(By.ID,"ke").send_keys("Selenium")
"""

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver.get('https://www.baidu.com')

#等待搜索按钮出现,最长等15秒,每0.5秒检查一次
wait = WebDriverWait(driver,timeout=15,poll_frequency=0.5)

#等待元素可点击
su_button = wait.until(
    EC.element_to_be_clickable((By.ID,"su"))
)

su_button.click()