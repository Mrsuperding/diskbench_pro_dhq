"""
Dashboard Page - 概览页面对象
============================
提供概览页面的元素定位器和操作方法

用法：
    from page_objects.dashboard.dashboard_page import DashboardPage

    def test_dashboard_stats(authenticated_page):
        dashboard = DashboardPage(authenticated_page)
        dashboard.goto()
        stats = dashboard.get_stats()
        assert stats["total_nodes"] > 0
"""
from typing import Optional, List, Dict
from playwright.sync_api import Page
from page_objects.base.base_page import BasePage


class DashboardSelectors:
    """概览页面选择器"""

    # ========== 页面标题 ==========
    PAGE_TITLE = "h1.page-title"
    PAGE_SUBTITLE = ".page-subtitle"

    # ========== 统计卡片 ==========
    STAT_CARD = ".stat-card"
    STAT_LABEL = ".stat-label"
    STAT_VALUE = ".stat-value"

    # 节点统计
    NODES_CARD = ".stat-card:has(.stat-label:text('节点'))"
    ONLINE_NODES_TAG = ".tag-success"
    OFFLINE_NODES_TAG = ".tag-danger"

    # 测试用例统计
    CASES_CARD = ".stat-card:has(.stat-label:text('测试用例'))"
    TEMPLATE_CASES_TAG = ".stat-footer.text-muted"

    # 测试任务统计
    TASKS_CARD = ".stat-card:has(.stat-label:text('测试任务'))"
    RUNNING_TASKS_TAG = ".tag-warning"

    # 用户统计
    USERS_CARD = ".stat-card:has(.stat-label:text('用户'))"
    ADMIN_USERS_TAG = ".stat-footer.text-muted"

    # ========== 快速入口 ==========
    QUICK_ACTIONS = ".quick-actions"
    QUICK_ITEM = ".quick-item"
    ADD_NODE_LINK = "a.quick-item:has(.quick-title:text('添加节点'))"
    CREATE_CASE_LINK = "a.quick-item:has(.quick-title:text('创建用例'))"
    START_TASK_LINK = "a.quick-item:has(.quick-title:text('启动任务'))"
    SCHEDULE_LINK = "a.quick-item:has(.quick-title:text('定时调度'))"
    BASELINE_LINK = "a.quick-item:has(.quick-title:text('性能基准'))"
    MONITOR_LINK = "a.quick-item:has(.quick-title:text('实时监控'))"

    # ========== 最近任务表格 ==========
    RECENT_TASKS_TABLE = ".data-table"
    TASK_TABLE_ROWS = ".data-table tbody tr"
    TASK_NAME_COLUMN = "td:nth-child(1)"
    TASK_STATUS_COLUMN = "td:nth-child(2)"
    TASK_TIME_COLUMN = "td:nth-child(3)"
    VIEW_ALL_LINK = "a:text('查看全部')"

    # ========== 系统信息 ==========
    SYS_INFO = ".sys-info"
    SYSTEM_UPTIME = ".sys-info-value"
    VERSION = ".sys-info-value:text('v1.2.0')"

    # ========== 操作按钮 ==========
    REFRESH_BUTTON = "button:has-text('刷新')"
    CREATE_TASK_BUTTON = "button:has-text('新建任务')"

    # ========== 状态标签 ==========
    TAG_SUCCESS = ".tag-success"
    TAG_WARNING = ".tag-warning"
    TAG_DANGER = ".tag-danger"
    TAG_INFO = ".tag-info"
    TAG_PENDING = ".tag-pending"

    # ========== 空状态 ==========
    EMPTY_STATE = ".text-muted:has-text('暂无')"


class DashboardPage(BasePage):
    """
    概览页面对象

    URL: /dashboard
    """

    URL = "/dashboard"

    def __init__(self, page: Page, timeout: int = 30000):
        super().__init__(page, timeout)
        self._selectors = DashboardSelectors()

    def goto(self, wait_until: str = "networkidle"):
        """导航到概览页"""
        super().goto(self.URL, wait_until)

    # ========== 统计卡片操作 ==========

    def get_stats(self) -> Dict[str, Dict[str, any]]:
        """
        获取所有统计卡片数据

        Returns:
            统计信息字典
        """
        stats = {}

        # 节点统计
        nodes_card = self.page.locator(self.selectors.NODES_CARD).first
        if nodes_card.is_visible():
            stat_label = nodes_card.locator(self.selectors.STAT_VALUE).first.inner_text()
            online_tag = nodes_card.locator(self.selectors.ONLINE_NODES_TAG).first
            offline_tag = nodes_card.locator(self.selectors.OFFLINE_NODES_TAG).first
            try:
                online_text = online_tag.inner_text() if online_tag.is_visible() else "0"
                offline_text = offline_tag.inner_text() if offline_tag.is_visible() else "0"
                stats["nodes"] = {
                    "total": int(stat_label) if stat_label.isdigit() else 0,
                    "online": int(''.join(filter(str.isdigit, online_text))) if online_text else 0,
                    "offline": int(''.join(filter(str.isdigit, offline_text))) if offline_text else 0,
                }
            except Exception:
                stats["nodes"] = {"total": 0, "online": 0, "offline": 0}

        # 测试用例统计
        cases_card = self.page.locator(self.selectors.CASES_CARD).first
        if cases_card.is_visible():
            try:
                stat_label = cases_card.locator(self.selectors.STAT_VALUE).first.inner_text()
                stats["cases"] = {
                    "total": int(stat_label) if stat_label.isdigit() else 0,
                }
            except Exception:
                stats["cases"] = {"total": 0}

        # 测试任务统计
        tasks_card = self.page.locator(self.selectors.TASKS_CARD).first
        if tasks_card.is_visible():
            try:
                stat_label = tasks_card.locator(self.selectors.STAT_VALUE).first.inner_text()
                running_tag = tasks_card.locator(self.selectors.RUNNING_TASKS_TAG).first
                running_text = running_tag.inner_text() if running_tag.is_visible() else "0"
                stats["tasks"] = {
                    "total": int(stat_label) if stat_label.isdigit() else 0,
                    "running": int(''.join(filter(str.isdigit, running_text))) if running_text else 0,
                }
            except Exception:
                stats["tasks"] = {"total": 0, "running": 0}

        # 用户统计
        users_card = self.page.locator(self.selectors.USERS_CARD).first
        if users_card.is_visible():
            try:
                stat_label = users_card.locator(self.selectors.STAT_VALUE).first.inner_text()
                stats["users"] = {
                    "total": int(stat_label) if stat_label.isdigit() else 0,
                }
            except Exception:
                stats["users"] = {"total": 0}

        return stats

    def get_total_nodes(self) -> int:
        """获取节点总数"""
        try:
            card = self.page.locator(self.selectors.NODES_CARD).first
            value = card.locator(self.selectors.STAT_VALUE).first.inner_text()
            return int(value) if value.isdigit() else 0
        except Exception:
            return 0

    def get_online_nodes(self) -> int:
        """获取在线节点数"""
        try:
            card = self.page.locator(self.selectors.NODES_CARD).first
            tag = card.locator(self.selectors.ONLINE_NODES_TAG).first
            text = tag.inner_text()
            return int(''.join(filter(str.isdigit, text))) if text else 0
        except Exception:
            return 0

    def get_total_tasks(self) -> int:
        """获取任务总数"""
        try:
            card = self.page.locator(self.selectors.TASKS_CARD).first
            value = card.locator(self.selectors.STAT_VALUE).first.inner_text()
            return int(value) if value.isdigit() else 0
        except Exception:
            return 0

    def get_running_tasks(self) -> int:
        """获取运行中任务数"""
        try:
            card = self.page.locator(self.selectors.TASKS_CARD).first
            tag = card.locator(self.selectors.RUNNING_TASKS_TAG).first
            text = tag.inner_text()
            return int(''.join(filter(str.isdigit, text))) if text else 0
        except Exception:
            return 0

    # ========== 最近任务表格 ==========

    def get_recent_tasks(self) -> List[Dict[str, str]]:
        """
        获取最近任务列表

        Returns:
            任务列表，每项包含 name, status, time
        """
        tasks = []
        rows = self.page.query_selector_all(self.selectors.TASK_TABLE_ROWS)

        for row in rows:
            try:
                name_cell = row.query_selector(self.selectors.TASK_NAME_COLUMN)
                status_cell = row.query_selector(self.selectors.TASK_STATUS_COLUMN)
                time_cell = row.query_selector(self.selectors.TASK_TIME_COLUMN)

                if name_cell:
                    tasks.append({
                        "name": name_cell.inner_text().strip(),
                        "status": status_cell.inner_text().strip() if status_cell else "",
                        "time": time_cell.inner_text().strip() if time_cell else "",
                    })
            except Exception:
                continue

        return tasks

    def get_recent_task_count(self) -> int:
        """获取最近任务数量"""
        rows = self.page.query_selector_all(self.selectors.TASK_TABLE_ROWS)
        # 过滤掉空状态行
        count = 0
        for row in rows:
            try:
                if row.query_selector(self.selectors.TASK_NAME_COLUMN):
                    count += 1
            except Exception:
                continue
        return count

    def is_recent_tasks_empty(self) -> bool:
        """检查最近任务是否为空"""
        return self.is_visible(self.selectors.EMPTY_STATE, timeout=3000)

    # ========== 快速入口 ==========

    def click_add_node(self):
        """点击添加节点入口"""
        self.click(self.selectors.ADD_NODE_LINK)

    def click_create_case(self):
        """点击创建用例入口"""
        self.click(self.selectors.CREATE_CASE_LINK)

    def click_start_task(self):
        """点击启动任务入口"""
        self.click(self.selectors.START_TASK_LINK)

    def click_schedule(self):
        """点击定时调度入口"""
        self.click(self.selectors.SCHEDULE_LINK)

    def click_baseline(self):
        """点击性能基准入口"""
        self.click(self.selectors.BASELINE_LINK)

    def click_monitor(self):
        """点击实时监控入口"""
        self.click(self.selectors.MONITOR_LINK)

    def click_view_all_tasks(self):
        """点击查看全部任务"""
        self.click(self.selectors.VIEW_ALL_LINK)

    # ========== 操作按钮 ==========

    def click_refresh(self):
        """点击刷新按钮"""
        self.click(self.selectors.REFRESH_BUTTON)
        self.wait.for_navigation()

    def click_create_task(self):
        """点击新建任务按钮"""
        self.click(self.selectors.CREATE_TASK_BUTTON)

    # ========== 系统信息 ==========

    def get_system_uptime(self) -> str:
        """获取系统运行时间"""
        try:
            uptime_elem = self.page.locator(self.selectors.SYSTEM_UPTIME).first
            return uptime_elem.inner_text()
        except Exception:
            return ""

    def get_version(self) -> str:
        """获取版本号"""
        try:
            version_elem = self.page.locator(self.selectors.VERSION).first
            return version_elem.inner_text()
        except Exception:
            return ""

    # ========== 等待方法 ==========

    def wait_for_stats_loaded(self, timeout: Optional[int] = None):
        """等待统计数据加载完成"""
        self.wait.for_visible(self.selectors.STAT_CARD, timeout)

    def wait_for_tasks_loaded(self, timeout: Optional[int] = None):
        """等待最近任务加载完成"""
        self.wait.for_element(self.selectors.TASK_TABLE_ROWS, timeout)
