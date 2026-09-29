# test_bing.py
import pytest
import allure
from pages.bing_page import BingPage


@allure.feature("必应搜索")
class TestBingSearch:
    """必应搜索功能自动化测试 — Allure 美化版"""

    @allure.story("首页加载")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.title("验证必应首页标题")
    @allure.description("打开必应首页，验证页面标题包含 'Bing' 或 '必应'")
    def test_homepage_title(self, driver):
        with allure.step("打开必应首页"):
            page = BingPage(driver)
            page.open()

        with allure.step("获取页面标题"):
            title = page.get_title()

        with allure.step("断言标题包含必应"):
            assert "Bing" in title or "必应" in title, f"首页标题异常: {title}"

        with allure.step("截图留证"):
            page.screenshot("test_homepage_title_bing.png")
            allure.attach(driver.get_screenshot_as_png(),
                          "首页截图", allure.attachment_type.PNG)

        allure.attach(str(title), "页面标题", allure.attachment_type.TEXT)

    @allure.story("关键词搜索")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("搜索关键词: {keyword}")
    @allure.description("验证输入关键词搜索后，结果页标题包含该关键词，且搜索结果不为空")
    @pytest.mark.parametrize("keyword, expected", [
        ("Python", "Python"),
        ("Selenium", "Selenium"),
        ("自动化测试", "自动化测试"),
    ])
    def test_search_keywords(self, driver, keyword, expected):
        page = BingPage(driver)

        with allure.step("打开必应首页"):
            page.open()

        with allure.step(f"输入关键词 '{keyword}' 并搜索"):
            page.search(keyword)

        with allure.step("验证标题包含关键词"):
            title = page.get_title()
            allure.attach(str(title), "搜索结果标题", allure.attachment_type.TEXT)
            assert expected in title, f"搜索'{keyword}'后标题不含预期: {title}"

        with allure.step("验证搜索结果数量 > 0"):
            count = page.get_result_count()
            allure.attach(str(count), "结果数量", allure.attachment_type.TEXT)
            assert count > 0, f"搜索'{keyword}'没有返回结果！"

        with allure.step("搜索页面截图"):
            page.screenshot(f"test_search_{keyword}_bing.png")
            allure.attach(driver.get_screenshot_as_png(),
                          f"搜索'{keyword}'截图", allure.attachment_type.PNG)

    @allure.story("URL 跳转")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("搜索后 URL 参数验证")
    @allure.description("搜索前后 URL 应发生变化，且包含搜索参数(q=)")
    def test_url_change_after_search(self, driver):
        page = BingPage(driver)

        with allure.step("打开必应首页并记录原始 URL"):
            page.open()
            original_url = driver.current_url
            allure.attach(str(original_url), "原始 URL", allure.attachment_type.TEXT)

        with allure.step("搜索 'Selenium自动化'"):
            page.search("Selenium自动化")

        with allure.step("验证 URL 变化"):
            new_url = driver.current_url
            allure.attach(str(new_url), "搜索后 URL", allure.attachment_type.TEXT)
            assert new_url != original_url, "搜索后URL没有变化！"
            assert "q=" in new_url or "search" in new_url.lower(), \
                   "URL中没有搜索关键词参数！"
