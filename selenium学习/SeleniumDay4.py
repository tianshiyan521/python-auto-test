from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
"""
from study.SeleniumDay1Test import search_box

driver = webdriver.Edge()

driver.get("https://www.baidu.com")
time.sleep(1)

#找到搜索框
search_box = driver.find_element(By.ID,"chat-submit-button")

#输入文字
search_box.send_keys("Selenium自动化")

#按Enter键搜索
search_box.send_keys(Keys.ENTER)

time.sleep(2)
driver.quit()
"""

"""
常用快捷键
Keys.ENTER 回车键
Keys.TAB tab键
Keys.ESCAPE ESC键
Keys.SPACE 空格键
keys.CONTROL + "a"   Ctrl+A 全选
Keys.CONTROL + "c"   Ctrl+C 复制
Keys.CONTROL + "v"   Ctrl+V 粘贴



from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

driver = webdriver.Edge()
driver.get("https://www.baidu.com")

#创建ActionChains对象
actions = ActionChains(driver)


#找到元素
search_box = driver.find_element(By.ID,'kw')

#鼠标悬停在搜索框上
actions.move_to_element(search_box).perform()

#右键点击
actions.context_click(search_box).perform()

#双击
actions.double_click(search_box).perform()

driver.quit()
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

driver = webdriver.Edge()
driver.get("https://www.baidu.com")

search_box = driver.find_element(By.ID,"chat-textarea")
search_box2 = driver.find_element(By.ID,"chat-textarea")

#输入   全选 复制
search_box.send_keys("hello Selenium")
actions = ActionChains(driver)
actions.click(search_box).perform()
actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
actions.key_down(Keys.CONTROL).send_keys("c").key_up(Keys.CONTROL).perform()

sleep(15)
#粘贴到另一个输入框
search_box2.click()
actions.key_down(Keys.CONTROL).send_keys("v").key_up(Keys.CONTROL).perform()

sleep(15)
driver.quit()

