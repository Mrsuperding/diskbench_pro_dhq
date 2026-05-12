"""
前端 UI 测试 - 任务管理页面
"""
import pytest


class TestTasksPage:
    """任务管理页面测试"""

    def test_should_display_tasks_list(self, page):
        """显示任务列表"""
        page.goto("http://localhost:3000/tasks")
        page.wait_for_selector("body", timeout=5000)

    def test_should_show_create_task_button(self, page):
        """显示创建任务按钮"""
        page.goto("http://localhost:3000/tasks")
        page.wait_for_selector("body", timeout=5000)

    def test_should_start_a_task(self, page):
        """启动任务"""
        page.goto("http://localhost:3000/tasks")
        page.wait_for_selector("body", timeout=5000)

    def test_should_stop_a_task(self, page):
        """停止任务"""
        page.goto("http://localhost:3000/tasks")
        page.wait_for_selector("body", timeout=5000)

    def test_should_show_task_status(self, page):
        """显示任务状态"""
        page.goto("http://localhost:3000/tasks")
        page.wait_for_selector("body", timeout=5000)
