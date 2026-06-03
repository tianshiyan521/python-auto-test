from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


driver = webdriver.Edge()

try:

    #示例1:处理下拉框
    driver.get("https://www.w3schools.com/tags/tryit.asp?filename=tryhtml_select")

    #切换到iframe(示例页面通常在iframe中)
    driver.switch_to.frame("iframeResult")

    #定位下拉框
    country_select = Select(driver.find_element(By.ID,"cars"))
    country_select.select_by_visible_text("Audi")
    print(f"选中:{country_select.first_selected_option.text}")

    #示例2:处理alert弹窗
    driver.get("https://www.w3schools.com/js/tryit.asp?filename=tryjs_alert")
    driver.switch_to.frame("iframeResult")

    #点击触发alert的按钮
    driver.find_element(By.XPATH,"//button[text()='Try it']").click()

    #等待alert出现并操作
    wait = WebDriverWait(driver,5)
    alert = wait.until(EC.alert_is_present())
    print(f"Alert文本:{alert.text}")
    alert.accept()#点击确认

    time.sleep(1)

finally:
    driver.quit()