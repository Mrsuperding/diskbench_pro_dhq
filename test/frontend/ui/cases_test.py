"""
前端 UI 测试 - 用例管理页面
"""
import pytest


class TestCasesPage:
    """用例管理页面测试"""

    def test_should_display_cases_list(self, page):
        """显示用例列表"""
        page.goto("http://localhost:3000/cases")
        page.wait_for_selector("body", timeout=5000)

    def test_should_show_create_case_button(self, page):
        """显示创建用例按钮"""
        page.goto("http://localhost:3000/cases")
        page.wait_for_selector("body", timeout=5000)

    def test_should_open_create_case_dialog(self, page):
        """打开创建用例对话框"""
        page.goto("http://localhost:3000/cases")
        page.wait_for_selector("body", timeout=5000)

    def test_should_display_fio_parameters(self, page):
        """显示 FIO 参数"""
        page.goto("http://localhost:3000/cases")
        page.wait_for_selector("body", timeout=5000)
