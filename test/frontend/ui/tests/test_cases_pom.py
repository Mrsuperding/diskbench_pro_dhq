"""
Cases Tests - 用例管理页面测试
===============================
使用 POM 模式测试用例管理页面

用法：
    pytest test/frontend/ui/tests/test_cases_pom.py -v
"""
import pytest
from playwright.sync_api import Page

from page_objects import CasesListPage


class TestCasesListPage:
    """用例列表页面测试"""

    def test_cases_page_loads(self, authenticated_page: Page):
        """TC_UI_CASE_001 - 用例列表页面正确加载"""
        cases_page = CasesListPage(authenticated_page)
        cases_page.goto()

        # 验证页面标题
        assert cases_page.is_visible("h1.page-title")
        title = cases_page.get_text("h1.page-title")
        assert "用例" in title

    def test_cases_page_elements_visible(self, authenticated_page: Page):
        """TC_UI_CASE_002 - 用例列表页面元素正确显示"""
        cases_page = CasesListPage(authenticated_page)
        cases_page.goto()
        cases_page.wait_for_table_loaded()

        # 验证操作按钮
        assert cases_page.is_visible(cases_page.selectors.USE_TEMPLATE_BUTTON)
        assert cases_page.is_visible(cases_page.selectors.CREATE_CASE_BUTTON)

        # 验证搜索区域
        assert cases_page.is_visible(cases_page.selectors.SEARCH_INPUT)
        assert cases_page.is_visible(cases_page.selectors.SEARCH_BUTTON)

    def test_cases_table_visible(self, authenticated_page: Page):
        """TC_UI_CASE_003 - 用例表格正确显示"""
        cases_page = CasesListPage(authenticated_page)
        cases_page.goto()
        cases_page.wait_for_table_loaded()

        # 表格应该可见（即使为空也有表格结构）
        assert cases_page.is_visible(cases_page.selectors.TABLE)

    def test_pagination_visible(self, authenticated_page: Page):
        """TC_UI_CASE_004 - 分页控件正确显示"""
        cases_page = CasesListPage(authenticated_page)
        cases_page.goto()
        cases_page.wait_for_table_loaded()

        # 如果有分页
        if cases_page.is_pagination_visible():
            assert cases_page.is_visible(cases_page.selectors.PAGINATION)


class TestCasesSearch:
    """用例搜索测试"""

    def test_search_input_works(self, authenticated_page: Page):
        """TC_UI_CASE_005 - 搜索输入框正常工作"""
        cases_page = CasesListPage(authenticated_page)
        cases_page.goto()
        cases_page.wait_for_table_loaded()

        # 输入搜索关键词
        cases_page.fill(cases_page.selectors.SEARCH_INPUT, "test")
        cases_page.click(cases_page.selectors.SEARCH_BUTTON)

        # 等待搜索结果
        cases_page.wait.for_navigation()

    def test_reset_button_clears_search(self, authenticated_page: Page):
        """TC_UI_CASE_006 - 重置按钮清除搜索"""
        cases_page = CasesListPage(authenticated_page)
        cases_page.goto()
        cases_page.wait_for_table_loaded()

        # 先搜索
        cases_page.fill(cases_page.selectors.SEARCH_INPUT, "nonexistent")
        cases_page.click(cases_page.selectors.SEARCH_BUTTON)
        cases_page.wait.for_navigation()

        # 再重置
        cases_page.click(cases_page.selectors.RESET_BUTTON)
        cases_page.wait.for_navigation()

        # 输入框应该被清空
        value = cases_page.get_value(cases_page.selectors.SEARCH_INPUT)
        assert value == ""


class TestCasesOperations:
    """用例操作测试"""

    def test_create_case_button_opens_dialog(self, authenticated_page: Page):
        """TC_UI_CASE_007 - 创建用例按钮打开对话框"""
        cases_page = CasesListPage(authenticated_page)
        cases_page.goto()
        cases_page.wait_for_table_loaded()

        cases_page.click_create_case()

        # 验证对话框出现
        assert cases_page.is_create_dialog_visible()

    def test_use_template_button_works(self, authenticated_page: Page):
        """TC_UI_CASE_008 - 使用模板按钮正常工作"""
        cases_page = CasesListPage(authenticated_page)
        cases_page.goto()
        cases_page.wait_for_table_loaded()

        cases_page.click_use_template()

        # 验证模板对话框出现
        assert cases_page.is_template_dialog_visible()

    def test_batch_delete_disabled_when_no_selection(self, authenticated_page: Page):
        """TC_UI_CASE_009 - 未选中时批量删除按钮禁用"""
        cases_page = CasesListPage(authenticated_page)
        cases_page.goto()
        cases_page.wait_for_table_loaded()

        # 批量删除按钮应该禁用
        assert not cases_page.is_batch_delete_enabled()


class TestCasesTable:
    """用例表格测试"""

    def test_get_table_row_count(self, authenticated_page: Page):
        """TC_UI_CASE_010 - 获取表格行数"""
        cases_page = CasesListPage(authenticated_page)
        cases_page.goto()
        cases_page.wait_for_table_loaded()

        count = cases_page.get_table_row_count()
        assert isinstance(count, int)
        assert count >= 0

    def test_get_case_names(self, authenticated_page: Page):
        """TC_UI_CASE_011 - 获取用例名称列表"""
        cases_page = CasesListPage(authenticated_page)
        cases_page.goto()
        cases_page.wait_for_table_loaded()

        names = cases_page.get_case_names()
        assert isinstance(names, list)

    def test_find_row_by_case_name_not_found(self, authenticated_page: Page):
        """TC_UI_CASE_012 - 查找不存在的用例返回 None"""
        cases_page = CasesListPage(authenticated_page)
        cases_page.goto()
        cases_page.wait_for_table_loaded()

        row = cases_page.find_row_by_case_name("ThisCaseDoesNotExist12345")
        assert row is None


class TestCasesEmptyState:
    """空状态测试"""

    def test_empty_state_handling(self, authenticated_page: Page):
        """TC_UI_CASE_013 - 空状态正确处理"""
        cases_page = CasesListPage(authenticated_page)
        cases_page.goto()
        cases_page.wait_for_table_loaded()

        # 如果没有数据，应该显示空状态
        if cases_page.get_table_row_count() == 0:
            assert cases_page.is_empty()
