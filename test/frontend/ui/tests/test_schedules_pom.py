"""
Schedules Tests - 定时调度页面测试
===================================
使用 POM 模式测试定时调度页面

用法：
    pytest test/frontend/ui/tests/test_schedules_pom.py -v
"""
import pytest
from playwright.sync_api import Page

from page_objects import SchedulesListPage


class TestSchedulesListPage:
    """定时调度页面测试"""

    def test_schedules_page_loads(self, authenticated_page: Page):
        """TC_UI_SCHED_001 - 定时调度页面正确加载"""
        schedules_page = SchedulesListPage(authenticated_page)
        schedules_page.goto()

        # 验证页面标题
        assert schedules_page.is_visible("h1.page-title")
        title = schedules_page.get_text("h1.page-title")
        assert "调度" in title

    def test_schedules_page_elements_visible(self, authenticated_page: Page):
        """TC_UI_SCHED_002 - 定时调度页面元素正确显示"""
        schedules_page = SchedulesListPage(authenticated_page)
        schedules_page.goto()
        schedules_page.wait_for_table_loaded()

        # 验证操作按钮
        assert schedules_page.is_visible(schedules_page.selectors.CREATE_SCHEDULE_BUTTON)

        # 验证表格
        assert schedules_page.is_visible(schedules_page.selectors.TABLE)

    def test_schedules_table_visible(self, authenticated_page: Page):
        """TC_UI_SCHED_003 - 调度表格正确显示"""
        schedules_page = SchedulesListPage(authenticated_page)
        schedules_page.goto()
        schedules_page.wait_for_table_loaded()

        # 表格应该可见
        assert schedules_page.is_visible(schedules_page.selectors.TABLE)


class TestSchedulesOperations:
    """调度操作测试"""

    def test_create_schedule_button_opens_dialog(self, authenticated_page: Page):
        """TC_UI_SCHED_004 - 创建调度按钮打开对话框"""
        schedules_page = SchedulesListPage(authenticated_page)
        schedules_page.goto()
        schedules_page.wait_for_table_loaded()

        schedules_page.click_create_schedule()

        # 验证对话框出现
        assert schedules_page.is_dialog_visible()

    def test_fill_schedule_form(self, authenticated_page: Page):
        """TC_UI_SCHED_005 - 填写调度表单"""
        schedules_page = SchedulesListPage(authenticated_page)
        schedules_page.goto()
        schedules_page.wait_for_table_loaded()

        # 打开对话框
        schedules_page.click_create_schedule()
        assert schedules_page.is_dialog_visible()

        # 填写表单
        schedules_page.fill_schedule_form(
            name="测试调度",
            template_task_id=1,
            trigger_type="interval",
            interval_minutes=60,
        )


class TestSchedulesTable:
    """调度表格测试"""

    def test_get_schedule_count(self, authenticated_page: Page):
        """TC_UI_SCHED_006 - 获取调度数量"""
        schedules_page = SchedulesListPage(authenticated_page)
        schedules_page.goto()
        schedules_page.wait_for_table_loaded()

        count = schedules_page.get_schedule_count()
        assert isinstance(count, int)
        assert count >= 0

    def test_get_schedules_returns_list(self, authenticated_page: Page):
        """TC_UI_SCHED_007 - 获取调度列表返回正确格式"""
        schedules_page = SchedulesListPage(authenticated_page)
        schedules_page.goto()
        schedules_page.wait_for_table_loaded()

        schedules = schedules_page.get_schedules()
        assert isinstance(schedules, list)

    def test_find_row_by_name_not_found(self, authenticated_page: Page):
        """TC_UI_SCHED_008 - 查找不存在的调度返回 None"""
        schedules_page = SchedulesListPage(authenticated_page)
        schedules_page.goto()
        schedules_page.wait_for_table_loaded()

        row = schedules_page.find_row_by_name("ThisScheduleDoesNotExist12345")
        assert row is None

    def test_is_schedule_enabled_returns_bool(self, authenticated_page: Page):
        """TC_UI_SCHED_009 - 调度启用状态返回布尔值"""
        schedules_page = SchedulesListPage(authenticated_page)
        schedules_page.goto()
        schedules_page.wait_for_table_loaded()

        # 获取一个调度
        schedules = schedules_page.get_schedules()
        if schedules:
            enabled = schedules_page.is_schedule_enabled(schedules[0]["name"])
            assert isinstance(enabled, bool)


class TestSchedulesDialog:
    """调度对话框测试"""

    def test_dialog_has_required_fields(self, authenticated_page: Page):
        """TC_UI_SCHED_010 - 对话框包含必填字段"""
        schedules_page = SchedulesListPage(authenticated_page)
        schedules_page.goto()
        schedules_page.wait_for_table_loaded()

        schedules_page.click_create_schedule()
        assert schedules_page.is_dialog_visible()

        # 验证必填字段
        assert schedules_page.is_visible(schedules_page.selectors.NAME_INPUT)
        assert schedules_page.is_visible(schedules_page.selectors.TEMPLATE_TASK_INPUT)
        assert schedules_page.is_visible(schedules_page.selectors.TRIGGER_RADIO_GROUP)

    def test_trigger_type_selection(self, authenticated_page: Page):
        """TC_UI_SCHED_011 - 触发类型选择"""
        schedules_page = SchedulesListPage(authenticated_page)
        schedules_page.goto()
        schedules_page.wait_for_table_loaded()

        schedules_page.click_create_schedule()
        assert schedules_page.is_dialog_visible()

        # 测试单次触发
        schedules_page.click(schedules_page.selectors.ONCE_RADIO)

        # 测试间隔触发
        schedules_page.click(schedules_page.selectors.INTERVAL_RADIO)

        # 测试 Cron 触发
        schedules_page.click(schedules_page.selectors.CRON_RADIO)


class TestSchedulesEmptyState:
    """空状态测试"""

    def test_empty_state_handling(self, authenticated_page: Page):
        """TC_UI_SCHED_012 - 空状态正确处理"""
        schedules_page = SchedulesListPage(authenticated_page)
        schedules_page.goto()
        schedules_page.wait_for_table_loaded()

        # 如果没有数据，应该显示空状态
        if schedules_page.get_schedule_count() == 0:
            assert schedules_page.is_empty()
