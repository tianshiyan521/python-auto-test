
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By

driver = webdriver.Edge()

#打开百度
driver.get("https://www.jju.edu.cn/")
print(f"Step1 页面标题:{driver.title}")



#2.在搜索框输入内容并搜索
search_box = driver.find_element(By.ID,"showkeycode1013825")
search_box.send_keys("九江学院")
driver.implicitly_wait(3)
driver.find_element(By.CLASS_NAME,"search-btn").click()
driver.implicitly_wait(10)

print(f"Step2 搜索结果页面标题:{driver.title}")
print(f"Step2 当前URL:{driver.current_url}")

#后退到百度首页
driver.back()
driver.implicitly_wait(10)
print(f"Step3 后退后标题:{driver.title}")

#前进回搜索结果
driver.forward()
driver.implicitly_wait(10)
print(f"Step4 前进后标题:{driver.title}")

#刷新页面
driver.refresh()
driver.implicitly_wait(10)
print(f"Step 刷新后标题:{driver.title}")

driver.quit()
print("练习完成!")

