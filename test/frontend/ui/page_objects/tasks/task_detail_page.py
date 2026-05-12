"""
Task Detail Page - 任务详情页面对象
==================================
提供任务详情页面的元素定位器和操作方法
"""
from typing import Optional, List
from playwright.sync_api import Page
from page_objects.base.base_page import BasePage


class TaskDetailSelectors:
    """任务详情页面选择器"""

    # ========== 页面头部 ==========
    BACK_BUTTON = 'button:has-text("← 返回")'
    TASK_TITLE = "h1"
    STATUS_TAG = ".status-pending, .status-running, .status-completed, .status-failed"

    # ========== 操作按钮 ==========
    START_BUTTON = 'button:has-text("启动")'
    STOP_BUTTON = 'button:has-text("停止")'
    DELETE_BUTTON = 'button:has-text("删除")'

    # ========== 指标卡片 ==========
    METRICS_ROW = ".metrics-row"
    METRIC_CARD = ".metric-card"
    METRIC_VALUE = ".metric-value"
    METRIC_LABEL = ".metric-label"

    # ========== Tab ==========
    TABS = ".el-tabs"
    TAB_INFO = '.el-tab-pane:has-text("基本信息")'
    TAB_NODES = '.el-tab-pane:has-text("节点")'
    TAB_CASE = '.el-tab-pane:has-text("用例")'
    TAB_LOGS = '.el-tab-pane:has-text("日志")'

    # ========== 基本信息 Tab ==========
    INFO_GRID = ".info-grid"
    INFO_ITEM = ".info-item"

    # ========== 节点 Tab ==========
    NODE_SECTION_HEADER = ".section-header"
    ADD_NODE_BUTTON = 'button:has-text("添加节点")'
    NODE_TABLE = ".el-table"
    NODE_TABLE_ROWS = ".el-table__body tr"
    REMOVE_NODE_BUTTON = 'button:has-text("移除")'

    # 添加节点对话框
    ADD_NODE_DIALOG = '.el-dialog:has-text("添加节点")'
    NODE_SELECT = '.el-dialog .el-select'
    PARTITION_SELECT = '.el-dialog .el-select >> nth=1'
    CONFIRM_ADD_BUTTON = '.el-dialog button:has-text("确定")'

    # ========== 用例 Tab ==========
    CASE_INFO = ".case-info"
    EDIT_CASE_BUTTON = 'button:has-text("编辑用例")'
    CASE_DESCRIPTIONS = ".el-descriptions"

    # 编辑用例对话框
    EDIT_CASE_DIALOG = '.el-dialog:has-text("编辑用例")'
    CASE_NAME_INPUT = '.el-dialog input[placeholder*="用例名称"] >> nth=0'
    SAVE_CASE_BUTTON = '.el-dialog button:has-text("保存")'

    # ========== 日志 Tab ==========
    LOG_LIST = ".log-list"
    LOG_ITEM = ".log-item"
    LOG_LEVEL = ".log-level"
    LOG_TIME = ".log-time"
    LOG_MSG = ".log-msg"
    REFRESH_LOGS_BUTTON = 'button:has-text("刷新") >> nth=1'

    # ========== 空状态 ==========
    EMPTY_STATE = ".empty"

    # ========== 确认对话框 ==========
    CONFIRM_DIALOG = ".el-message-box"
    CONFIRM_BUTTON = 'button:has-text("确定")'
    CANCEL_BUTTON = 'button:has-text("取消")'


class TaskDetailPage(BasePage):
    """
    任务详情页面对象

    URL: /tasks/{id}
    """

    URL = "/tasks"

    def __init__(self, page: Page, timeout: int = 30000):
        super().__init__(page, timeout)
        self._selectors = TaskDetailSelectors()

    def goto_task_detail(self, task_id: int, wait_until: str = "networkidle"):
        """导航到任务详情页"""
        super().goto(f"{self.URL}/{task_id}", wait_until)

    # ========== 页面元素检查 ==========

    def is_header_visible(self) -> bool:
        """检查头部是否可见"""
        return self.is_visible(self.selectors.TASK_TITLE, timeout=5000)

    def is_metrics_visible(self) -> bool:
        """检查指标卡片是否可见"""
        return self.is_visible(self.selectors.METRICS_ROW, timeout=5000)

    def is_tabs_visible(self) -> bool:
        """检查 Tab 是否可见"""
        return self.is_visible(self.selectors.TABS, timeout=5000)

    # ========== 头部操作 ==========

    def click_back(self):
        """点击返回按钮"""
        self.click(self.selectors.BACK_BUTTON)
        self.wait.for_url(f"**{self.URL}**")

    def click_start(self):
        """点击启动按钮"""
        self.click(self.selectors.START_BUTTON)

    def click_stop(self):
        """点击停止按钮"""
        self.click(self.selectors.STOP_BUTTON)

    def click_delete(self):
        """点击删除按钮"""
        self.click(self.selectors.DELETE_BUTTON)

    # ========== 指标获取 ==========

    def get_metric_values(self) -> dict:
        """获取所有指标值"""
        metrics = {}
        cards = self.page.query_selector_all(self.selectors.METRIC_CARD)
        for card in cards:
            try:
                label = card.query_selector(self.selectors.METRIC_LABEL)
                value = card.query_selector(self.selectors.METRIC_VALUE)
                if label and value:
                    metrics[label.inner_text().strip()] = value.inner_text().strip()
            except Exception:
                continue
        return metrics

    # ========== Tab 操作 ==========

    def click_tab(self, tab_name: str):
        """
        点击 Tab

        Args:
            tab_name: info/nodes/case/logs
        """
        tab_map = {
            "info": 'span:has-text("基本信息")',
            "nodes": 'span:has-text("节点")',
            "case": 'span:has-text("用例")',
            "logs": 'span:has-text("日志")'
        }
        selector = tab_map.get(tab_name)
        if selector:
            self.click(selector)
            self.wait.for_timeout(500)

    # ========== 节点 Tab ==========

    def is_node_tab_visible(self) -> bool:
        """检查节点 Tab 内容是否可见"""
        self.click_tab("nodes")
        return self.is_visible(self.selectors.NODE_TABLE, timeout=5000)

    def get_node_count(self) -> int:
        """获取节点数量"""
        self.click_tab("nodes")
        rows = self.page.query_selector_all(self.selectors.NODE_TABLE_ROWS)
        return len(rows) if rows else 0

    def click_add_node(self):
        """点击添加节点按钮"""
        self.click(self.selectors.ADD_NODE_BUTTON)

    def is_add_node_dialog_visible(self) -> bool:
        """检查添加节点对话框是否可见"""
        return self.is_visible(self.selectors.ADD_NODE_DIALOG, timeout=5000)

    def select_node_in_dialog(self, node_name: str):
        """在对话框中选择节点"""
        self.click(self.selectors.NODE_SELECT)
        self.wait.for_visible('.el-select-dropdown')
        items = self.page.query_selector_all('.el-select-dropdown__item')
        for item in items:
            if node_name in item.inner_text():
                item.click()
                return
        raise ValueError(f"Node not found: {node_name}")

    def select_partition_in_dialog(self, partition_text: str):
        """在对话框中选择分区"""
        self.click(self.selectors.PARTITION_SELECT)
        self.wait.for_visible('.el-select-dropdown')
        items = self.page.query_selector_all('.el-select-dropdown__item')
        for item in items:
            if partition_text in item.inner_text():
                item.click()
                return

    def confirm_add_node(self):
        """确认添加节点"""
        self.click(self.selectors.CONFIRM_ADD_BUTTON)

    def click_remove_node(self, index: int = 0):
        """点击移除节点按钮"""
        buttons = self.page.query_selector_all(self.selectors.REMOVE_NODE_BUTTON)
        if len(buttons) > index:
            buttons[index].click()

    # ========== 用例 Tab ==========

    def is_case_tab_visible(self) -> bool:
        """检查用例 Tab 内容是否可见"""
        self.click_tab("case")
        return self.is_visible(self.selectors.CASE_INFO, timeout=5000)

    def click_edit_case(self):
        """点击编辑用例按钮"""
        self.click(self.selectors.EDIT_CASE_BUTTON)

    def is_edit_case_dialog_visible(self) -> bool:
        """检查编辑用例对话框是否可见"""
        return self.is_visible(self.selectors.EDIT_CASE_DIALOG, timeout=5000)

    def get_case_field(self, field_label: str) -> Optional[str]:
        """获取用例字段值"""
        self.click_tab("case")
        labels = self.page.query_selector_all('.el-descriptions__label')
        for label in labels:
            if field_label in label.inner_text():
                td = label.evaluate_handle("el => el.parentElement.querySelector('.el-descriptions__content')")
                if td:
                    return td.inner_text()
        return None

    def save_case(self):
        """保存用例"""
        self.click(self.selectors.SAVE_CASE_BUTTON)

    # ========== 日志 Tab ==========

    def is_logs_tab_visible(self) -> bool:
        """检查日志 Tab 内容是否可见"""
        self.click_tab("logs")
        return self.is_visible(self.selectors.LOG_LIST, timeout=5000)

    def get_log_count(self) -> int:
        """获取日志数量"""
        self.click_tab("logs")
        logs = self.page.query_selector_all(self.selectors.LOG_ITEM)
        return len(logs) if logs else 0

    def get_logs(self) -> List[dict]:
        """获取所有日志"""
        self.click_tab("logs")
        logs = []
        items = self.page.query_selector_all(self.selectors.LOG_ITEM)
        for item in items:
            try:
                level = item.query_selector(self.selectors.LOG_LEVEL)
                time = item.query_selector(self.selectors.LOG_TIME)
                msg = item.query_selector(self.selectors.LOG_MSG)
                logs.append({
                    "level": level.inner_text().strip() if level else "",
                    "time": time.inner_text().strip() if time else "",
                    "message": msg.inner_text().strip() if msg else ""
                })
            except Exception:
                continue
        return logs

    def click_refresh_logs(self):
        """点击刷新日志按钮"""
        self.click(self.selectors.REFRESH_LOGS_BUTTON)

    # ========== 确认对话框 ==========

    def confirm_action(self):
        """确认操作"""
        self.wait.for_visible(self.selectors.CONFIRM_DIALOG)
        self.click(self.selectors.CONFIRM_BUTTON)

    def cancel_action(self):
        """取消操作"""
        self.wait.for_visible(self.selectors.CONFIRM_DIALOG)
        self.click(self.selectors.CANCEL_BUTTON)

    # ========== 基本信息 ==========

    def get_task_info(self) -> dict:
        """获取任务基本信息"""
        self.click_tab("info")
        info = {}
        items = self.page.query_selector_all(self.selectors.INFO_ITEM)
        for item in items:
            try:
                label = item.query_selector('.label')
                value = item.query_selector('span:last-child')
                if label and value:
                    info[label.inner_text().strip()] = value.inner_text().strip()
            except Exception:
                continue
        return info

    def get_status(self) -> str:
        """获取任务状态"""
        status = self.page.query_selector(self.selectors.STATUS_TAG)
        return status.inner_text().strip() if status else ""
