from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Edge()
driver.get("https://www.jju.edu.cn")

#找到搜索框并输入文字
search_box = driver.find_element(By.ID,"kw")
search_box.send_keys("Selenium自动化")
#点击元素
search_btn = driver.find_element(By.ID,"su")
search_btn.click()

#清空后再重新输入
search_box.clear()
search_box.send_keys("新的搜索词")


#提交表单
#有些表单可以用submit提交(相当于按回车)
search_box.submit()

