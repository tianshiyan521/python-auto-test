import time, os
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BingPage:
    """必应首页 POM 对象"""

    URL = "https://cn.bing.com"
    SEARCH_INPUT = (By.ID, "sb_form_q")
    SEARCH_ICON = (By.ID, "search_icon")
    RESULT_ITEMS = (By.CSS_SELECTOR, "#b_results .b_algo")

    def __init__(self, driver):
        self.driver = driver

    def open(self):
        self.driver.get(self.URL)
        return self

    def get_title(self):
        return self.driver.title

    def search(self, keyword):
        wait = WebDriverWait(self.driver, 10)
        input_box = wait.until(EC.presence_of_element_located(self.SEARCH_INPUT))
        input_box.clear()
        input_box.send_keys(keyword)
        input_box.send_keys(Keys.RETURN)
        wait.until(EC.presence_of_element_located(self.RESULT_ITEMS))
        time.sleep(0.5)

    def get_result_count(self):
        results = self.driver.find_elements(*self.RESULT_ITEMS)
        return len(results)

    def screenshot(self, filename):
        save_dir = os.path.join(os.path.dirname(__file__), "..", "截图")
        os.makedirs(save_dir, exist_ok=True)
        path = os.path.join(save_dir, filename)
        self.driver.save_screenshot(path)
