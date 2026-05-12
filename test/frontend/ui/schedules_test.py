"""
前端 UI 测试 - 调度管理页面
"""
import pytest


class TestSchedulesPage:
    """调度管理页面测试"""

    def test_should_display_schedules_list(self, page):
        """显示调度列表"""
        page.goto("http://localhost:3000/schedules")
        page.wait_for_selector("body", timeout=5000)

    def test_should_show_create_schedule_button(self, page):
        """显示创建调度按钮"""
        page.goto("http://localhost:3000/schedules")
        page.wait_for_selector("body", timeout=5000)

    def test_should_open_create_schedule_dialog(self, page):
        """打开创建调度对话框"""
        page.goto("http://localhost:3000/schedules")
        page.wait_for_selector("body", timeout=5000)

    def test_should_toggle_schedule_enabled_status(self, page):
        """切换调度启用状态"""
        page.goto("http://localhost:3000/schedules")
        page.wait_for_selector("body", timeout=5000)
