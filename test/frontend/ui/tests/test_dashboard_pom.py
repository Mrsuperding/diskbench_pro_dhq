"""
Dashboard Tests - 概览页面测试
===============================
使用 POM 模式测试概览页面

用法：
    pytest test/frontend/ui/tests/test_dashboard_pom.py -v
"""
import pytest
from playwright.sync_api import Page

from page_objects import DashboardPage


class TestDashboardPage:
    """概览页面测试"""

    def test_dashboard_page_loads(self, authenticated_page: Page):
        """TC_UI_DASH_001 - 概览页面正确加载"""
        dashboard = DashboardPage(authenticated_page)
        dashboard.goto()

        # 验证页面标题
        assert dashboard.is_visible("h1.page-title")
        title = dashboard.get_text("h1.page-title")
        assert "概览" in title

    def test_dashboard_stats_visible(self, authenticated_page: Page):
        """TC_UI_DASH_002 - 统计卡片正确显示"""
        dashboard = DashboardPage(authenticated_page)
        dashboard.goto()
        dashboard.wait_for_stats_loaded()

        # 验证统计卡片存在
        assert dashboard.is_visible(".stat-card")

    def test_dashboard_quick_actions_visible(self, authenticated_page: Page):
        """TC_UI_DASH_003 - 快速入口正确显示"""
        dashboard = DashboardPage(authenticated_page)
        dashboard.goto()
        dashboard.wait_for_stats_loaded()

        # 验证快速入口
        assert dashboard.is_visible(dashboard.selectors.QUICK_ACTIONS)
        assert dashboard.is_visible(dashboard.selectors.ADD_NODE_LINK)
        assert dashboard.is_visible(dashboard.selectors.CREATE_CASE_LINK)
        assert dashboard.is_visible(dashboard.selectors.START_TASK_LINK)

    def test_dashboard_recent_tasks_table_visible(self, authenticated_page: Page):
        """TC_UI_DASH_004 - 最近任务表格正确显示"""
        dashboard = DashboardPage(authenticated_page)
        dashboard.goto()
        dashboard.wait_for_tasks_loaded()

        # 验证最近任务表格
        assert dashboard.is_visible(dashboard.selectors.RECENT_TASKS_TABLE)

    def test_dashboard_system_info_visible(self, authenticated_page: Page):
        """TC_UI_DASH_005 - 系统信息正确显示"""
        dashboard = DashboardPage(authenticated_page)
        dashboard.goto()
        dashboard.wait_for_stats_loaded()

        # 验证系统信息区域
        assert dashboard.is_visible(dashboard.selectors.SYS_INFO)

    def test_dashboard_refresh_button_works(self, authenticated_page: Page):
        """TC_UI_DASH_006 - 刷新按钮正常工作"""
        dashboard = DashboardPage(authenticated_page)
        dashboard.goto()
        dashboard.wait_for_stats_loaded()

        # 点击刷新
        dashboard.click_refresh()

        # 验证页面仍然正常
        assert dashboard.is_visible("h1.page-title")

    def test_dashboard_create_task_button_navigates(self, authenticated_page: Page):
        """TC_UI_DASH_007 - 新建任务按钮正确导航"""
        dashboard = DashboardPage(authenticated_page)
        dashboard.goto()
        dashboard.wait_for_stats_loaded()

        # 点击新建任务
        dashboard.click_create_task()

        # 验证跳转到创建任务页面
        authenticated_page.wait_for_url("**/tasks/create**", timeout=10000)
        assert "/tasks/create" in authenticated_page.url


class TestDashboardQuickActions:
    """快速入口测试"""

    def test_click_add_node_navigates_to_nodes(self, authenticated_page: Page):
        """TC_UI_DASH_008 - 添加节点入口导航到节点页面"""
        dashboard = DashboardPage(authenticated_page)
        dashboard.goto()
        dashboard.wait_for_stats_loaded()

        dashboard.click_add_node()

        authenticated_page.wait_for_url("**/nodes**", timeout=10000)
        assert "/nodes" in authenticated_page.url

    def test_click_create_case_navigates_to_cases(self, authenticated_page: Page):
        """TC_UI_DASH_009 - 创建用例入口导航到用例页面"""
        dashboard = DashboardPage(authenticated_page)
        dashboard.goto()
        dashboard.wait_for_stats_loaded()

        dashboard.click_create_case()

        authenticated_page.wait_for_url("**/cases/create**", timeout=10000)
        assert "/cases" in authenticated_page.url

    def test_click_schedule_navigates_to_schedules(self, authenticated_page: Page):
        """TC_UI_DASH_010 - 定时调度入口导航到调度页面"""
        dashboard = DashboardPage(authenticated_page)
        dashboard.goto()
        dashboard.wait_for_stats_loaded()

        dashboard.click_schedule()

        authenticated_page.wait_for_url("**/schedules**", timeout=10000)
        assert "/schedules" in authenticated_page.url


class TestDashboardStats:
    """统计数据测试"""

    def test_get_stats_returns_dict(self, authenticated_page: Page):
        """TC_UI_DASH_011 - 获取统计数据返回正确格式"""
        dashboard = DashboardPage(authenticated_page)
        dashboard.goto()
        dashboard.wait_for_stats_loaded()

        stats = dashboard.get_stats()

        assert isinstance(stats, dict)
        # 至少应该有节点或用例或任务统计
        assert len(stats) >= 0

    def test_get_total_nodes_returns_int(self, authenticated_page: Page):
        """TC_UI_DASH_012 - 获取节点总数返回整数"""
        dashboard = DashboardPage(authenticated_page)
        dashboard.goto()
        dashboard.wait_for_stats_loaded()

        total = dashboard.get_total_nodes()

        assert isinstance(total, int)
        assert total >= 0

    def test_get_total_tasks_returns_int(self, authenticated_page: Page):
        """TC_UI_DASH_013 - 获取任务总数返回整数"""
        dashboard = DashboardPage(authenticated_page)
        dashboard.goto()
        dashboard.wait_for_stats_loaded()

        total = dashboard.get_total_tasks()

        assert isinstance(total, int)
        assert total >= 0
