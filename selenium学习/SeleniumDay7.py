'''


from airtest.core.win.screen import screenshot
from selenium import webdriver
from selenium.webdriver.common.by import By
import os

driver = webdriver.Edge()
driver.get("https://www.baidu.com")

#截图保存为文件(返回True/False表示是否成功)

screenshot_path = os.path.join(os.getcwd(),"baidu_screenshot.png")
result = driver.get_screenshot_as_file(screenshot_path)
print(f"截图保存{'成功' if result else '失败'}:{screenshot_path}")

driver.quit()


from selenium import webdriver

driver = webdriver.Edge()
driver.get("https:www.baidu.com")

#获取截图的二进制数据(PNG格式)
png_data = driver.get_screenshot_as_png()
print(f"截图数据大小:{len(png_data)} bytes")

#可以写入文件
with open("screenshot_binatry.png","wb") as f:
    f.write(png_data)

driver.quit()


from selenium import webdriver

driver = webdriver.Edge()
driver.get("https://www.baidu.com")

#获取Base64编码的截图
base64_str = driver.get_screenshot_as_base64()
print(f"Base64长度:{len(base64_str)}")

driver.quit()


from selenium import webdriver
from selenium.webdriver.common.by import By

from practice_run import search_box

driver = webdriver.Edge()
driver.get("https://www.baidu.com")

#定位搜索框元素并截图
search_box = driver.find_element(By.ID,"kw")
search_box.screenshot(("element_screenshot.png"))
print("元素已保存")

driver.quit()
'''
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Edge()
driver.get("https://the-internet.herokuapp.com/upload")

#直接向<input type="file">元素发文件路径
file_input = driver.find_element(By.ID,"file-upload")
file_input.send_keys(r"C:\Users\Administrator\test_upload.txt")

#点击上传按钮
driver.find_element(By.ID,"file-submit").click()

#验证上传成功
msg = driver.find_element(By.ID,"uploaded-files").text
print(f"上传的文件:{msg}")

driver.quit()