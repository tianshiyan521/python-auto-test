import unittest
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BaiduTest(unittest.TestCase):
    #百度搜索测试类

    def setUp(self):
        #每个测试方法执行前自动调用
        self.driver = webdriver.Edge()
        self.driver.maximize_window()
        self.driver.implicitly_wait(5)

    def tearDown(self):
        #每个测试方法执行后自动调用 -- 关闭浏览器
        self.driver.quit()

    def test_baidu_title(self):
        #测试百度首页标题
        self.driver.get("https://www.baidu.com")
        self.assertIn("百度",self.driver.title)

    def test_baidu_search(self):
        #测试搜索功能
        self.driver.get("https://www.baidu.com")
        search_box = self.driver.find_element(By.ID,"chat-textarea")
        search_box.send_keys("Selenium自动化测试")
        self.driver.find_element(By.ID,"chat-submit-button").click()

        #等待搜索结果出现
        WebDriverWait(self.driver,10).until(
            EC.presence_of_element_located((By.ID,"content_left"))
        )

        #断言:搜索结果页URL包含关键词
        self.assertIn("Selenium",self.driver.current_url)


if __name__ == "__main__":
    unittest.main()
