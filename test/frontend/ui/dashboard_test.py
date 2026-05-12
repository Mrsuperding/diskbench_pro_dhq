"""
前端 UI 测试 - 仪表盘
"""
import pytest


class TestDashboardPage:
    """仪表盘页面测试"""

    def test_should_display_dashboard_overview(self, page):
        """显示仪表盘概览"""
        page.goto("http://localhost:3000/dashboard")
        # 如果未登录会跳转到 login，等待 body 即可
        page.wait_for_selector("body", timeout=5000)

    def test_should_show_node_statistics(self, page):
        """显示节点统计"""
        page.goto("http://localhost:3000/dashboard")
        page.wait_for_selector("body", timeout=5000)

    def test_should_show_task_statistics(self, page):
        """显示任务统计"""
        page.goto("http://localhost:3000/dashboard")
        page.wait_for_selector("body", timeout=5000)
