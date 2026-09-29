import pytest
import allure
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """每个测试阶段结束后触发，用于失败时自动截图"""
    outcome = yield
    report = outcome.get_result()

    # 仅关注测试执行阶段(call)，且用例失败时
    if report.when == "call" and report.failed:
        driver = item.funcargs.get("driver")
        if driver:
            try:
                screenshot = driver.get_screenshot_as_png()
                allure.attach(screenshot,
                              f"失败截图 - {item.name}",
                              allure.attachment_type.PNG)
            except Exception:
                pass  # 截图失败不影响报告生成


@pytest.fixture(scope="function")
def driver():
    """每个测试函数独立的 Edge 驱动"""
    service = EdgeService(executable_path="C:/Users/Administrator/WorkBuddy/Claw/msedgedriver.exe")
    drv = webdriver.Edge(service=service)
    drv.maximize_window()
    drv.implicitly_wait(5)
    yield drv
    drv.quit()
