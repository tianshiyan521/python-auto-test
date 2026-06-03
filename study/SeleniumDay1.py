from selenium import webdriver
from selenium.webdriver.edge.service import Service

driver = webdriver.Edge()

#打开网页
driver.get("https:www.baidu.com")

#后退
driver.back()

#前进
driver.forward()

#刷新
driver.refresh()

#最大化窗口
driver.maximize_window()

#设置窗口大小(宽,高)
driver.set_window_size()

#获取当前窗口大小
size = driver.get_window_size()
print(size)

#当前URL
url = driver.current_url
print(f"当前页面URL:{url}")

#页面标题
title = driver.title
print(f"页面标题:{title}")

#页面源码(HTML)
html = driver.page_source
print(f"页面长度:{len(html)}字符")

driver.quit()