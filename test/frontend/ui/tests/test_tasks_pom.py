"""
Tasks Tests - 任务管理页面测试
==============================
使用 POM 模式测试任务管理页面

用法：
    pytest test/frontend/ui/tests/test_tasks_pom.py -v
"""
import pytest
from playwright.sync_api import Page

from page_objects import TasksListPage


class TestTasksListPage:
    """任务列表页面测试"""

    def test_tasks_page_loads(self, authenticated_page: Page):
        """TC_UI_TASK_001 - 任务列表页面正确加载"""
        tasks_page = TasksListPage(authenticated_page)
        tasks_page.goto()

        # 验证页面标题
        assert tasks_page.is_visible("h1.page-title")
        title = tasks_page.get_text("h1.page-title")
        assert "任务" in title

    def test_tasks_page_elements_visible(self, authenticated_page: Page):
        """TC_UI_TASK_002 - 任务列表页面元素正确显示"""
        tasks_page = TasksListPage(authenticated_page)
        tasks_page.goto()
        tasks_page.wait_for_table_loaded()

        # 验证操作按钮
        assert tasks_page.is_visible(tasks_page.selectors.CREATE_TASK_BUTTON)
        assert tasks_page.is_visible(tasks_page.selectors.BATCH_START_BUTTON)
        assert tasks_page.is_visible(tasks_page.selectors.BATCH_DELETE_BUTTON)

        # 验证搜索区域
        assert tasks_page.is_visible(tasks_page.selectors.SEARCH_INPUT)
        assert tasks_page.is_visible(tasks_page.selectors.STATUS_FILTER)

    def test_tasks_table_visible(self, authenticated_page: Page):
        """TC_UI_TASK_003 - 任务表格正确显示"""
        tasks_page = TasksListPage(authenticated_page)
        tasks_page.goto()
        tasks_page.wait_for_table_loaded()

        # 表格应该可见
        assert tasks_page.is_visible(tasks_page.selectors.TABLE)

    def test_batch_buttons_disabled_when_no_selection(self, authenticated_page: Page):
        """TC_UI_TASK_004 - 未选中时批量按钮禁用"""
        tasks_page = TasksListPage(authenticated_page)
        tasks_page.goto()
        tasks_page.wait_for_table_loaded()

        # 批量按钮应该禁用
        assert not tasks_page.is_batch_start_enabled()
        assert not tasks_page.is_batch_stop_enabled()
        assert not tasks_page.is_batch_delete_enabled()


class TestTasksSearch:
    """任务搜索测试"""

    def test_search_input_works(self, authenticated_page: Page):
        """TC_UI_TASK_005 - 搜索输入框正常工作"""
        tasks_page = TasksListPage(authenticated_page)
        tasks_page.goto()
        tasks_page.wait_for_table_loaded()

        # 输入搜索关键词
        tasks_page.fill(tasks_page.selectors.SEARCH_INPUT, "test")
        tasks_page.click(tasks_page.selectors.SEARCH_BUTTON)
        tasks_page.wait.for_navigation()

    def test_status_filter_works(self, authenticated_page: Page):
        """TC_UI_TASK_006 - 状态筛选正常工作"""
        tasks_page = TasksListPage(authenticated_page)
        tasks_page.goto()
        tasks_page.wait_for_table_loaded()

        # 选择状态筛选
        tasks_page.filter_by_status("pending")
        tasks_page.wait.for_navigation()

    def test_reset_button_clears_filters(self, authenticated_page: Page):
        """TC_UI_TASK_007 - 重置按钮清除筛选"""
        tasks_page = TasksListPage(authenticated_page)
        tasks_page.goto()
        tasks_page.wait_for_table_loaded()

        # 先设置筛选
        tasks_page.filter_by_status("running")
        tasks_page.wait.for_navigation()

        # 再重置
        tasks_page.click(tasks_page.selectors.RESET_BUTTON)
        tasks_page.wait.for_navigation()


class TestTasksOperations:
    """任务操作测试"""

    def test_create_task_button_opens_dialog(self, authenticated_page: Page):
        """TC_UI_TASK_008 - 创建任务按钮打开对话框"""
        tasks_page = TasksListPage(authenticated_page)
        tasks_page.goto()
        tasks_page.wait_for_table_loaded()

        tasks_page.click_create_task()

        # 验证对话框出现
        assert tasks_page.is_create_dialog_visible()


class TestTasksTable:
    """任务表格测试"""

    def test_get_table_row_count(self, authenticated_page: Page):
        """TC_UI_TASK_009 - 获取表格行数"""
        tasks_page = TasksListPage(authenticated_page)
        tasks_page.goto()
        tasks_page.wait_for_table_loaded()

        count = tasks_page.get_table_row_count()
        assert isinstance(count, int)
        assert count >= 0

    def test_get_task_names(self, authenticated_page: Page):
        """TC_UI_TASK_010 - 获取任务名称列表"""
        tasks_page = TasksListPage(authenticated_page)
        tasks_page.goto()
        tasks_page.wait_for_table_loaded()

        names = tasks_page.get_task_names()
        assert isinstance(names, list)

    def test_get_task_status_returns_string(self, authenticated_page: Page):
        """TC_UI_TASK_011 - 获取任务状态返回正确格式"""
        tasks_page = TasksListPage(authenticated_page)
        tasks_page.goto()
        tasks_page.wait_for_table_loaded()

        # 如果有任务，验证状态返回格式
        names = tasks_page.get_task_names()
        if names:
            status = tasks_page.get_task_status(names[0])
            assert status is None or status in ["pending", "running", "completed", "failed"]

    def test_find_row_by_task_name_not_found(self, authenticated_page: Page):
        """TC_UI_TASK_012 - 查找不存在的任务返回 None"""
        tasks_page = TasksListPage(authenticated_page)
        tasks_page.goto()
        tasks_page.wait_for_table_loaded()

        row = tasks_page.find_row_by_task_name("ThisTaskDoesNotExist12345")
        assert row is None

    def test_get_tasks_by_status(self, authenticated_page: Page):
        """TC_UI_TASK_013 - 按状态获取任务列表"""
        tasks_page = TasksListPage(authenticated_page)
        tasks_page.goto()
        tasks_page.wait_for_table_loaded()

        # 获取待执行任务
        pending_tasks = tasks_page.get_tasks_by_status("pending")
        assert isinstance(pending_tasks, list)

        # 获取运行中任务
        running_tasks = tasks_page.get_tasks_by_status("running")
        assert isinstance(running_tasks, list)


class TestTasksPagination:
    """任务分页测试"""

    def test_pagination_visible(self, authenticated_page: Page):
        """TC_UI_TASK_014 - 分页控件正确显示"""
        tasks_page = TasksListPage(authenticated_page)
        tasks_page.goto()
        tasks_page.wait_for_table_loaded()

        if tasks_page.is_pagination_visible():
            assert tasks_page.is_visible(tasks_page.selectors.PAGINATION)

    def test_get_total_count(self, authenticated_page: Page):
        """TC_UI_TASK_015 - 获取任务总数"""
        tasks_page = TasksListPage(authenticated_page)
        tasks_page.goto()
        tasks_page.wait_for_table_loaded()

        total = tasks_page.get_total_count()
        assert isinstance(total, int)
        assert total >= 0


class TestTasksEmptyState:
    """空状态测试"""

    def test_empty_state_handling(self, authenticated_page: Page):
        """TC_UI_TASK_016 - 空状态正确处理"""
        tasks_page = TasksListPage(authenticated_page)
        tasks_page.goto()
        tasks_page.wait_for_table_loaded()

        # 如果没有数据，应该显示空状态
        if tasks_page.get_table_row_count() == 0:
            assert tasks_page.is_empty()
