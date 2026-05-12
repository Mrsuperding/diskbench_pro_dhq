"""
Tasks List Page - 任务列表页面对象
==================================
提供任务管理页面的元素定位器和操作方法

用法：
    from page_objects.tasks.tasks_list_page import TasksListPage

    def test_tasks_list(authenticated_page):
        tasks_page = TasksListPage(authenticated_page)
        tasks_page.goto()
        count = tasks_page.get_table_row_count()
"""
from typing import Optional, List, Dict
from playwright.sync_api import Page
from page_objects.base.base_page import BasePage


class TasksListSelectors:
    """任务列表页面选择器"""

    # ========== 页面标题 ==========
    PAGE_TITLE = "h1.page-title"
    PAGE_SUBTITLE = ".page-subtitle"

    # ========== 操作按钮 ==========
    BATCH_START_BUTTON = 'button:has-text("批量启动")'
    BATCH_STOP_BUTTON = 'button:has-text("批量停止")'
    BATCH_DELETE_BUTTON = 'button:has-text("批量删除")'
    CREATE_TASK_BUTTON = 'button:has-text("创建任务")'

    # ========== 搜索和筛选 ==========
    SEARCH_INPUT = 'input[placeholder="搜索任务名称"]'
    STATUS_FILTER = '.w-32.el-select'
    SEARCH_BUTTON = 'button:has-text("搜索")'
    RESET_BUTTON = 'button:has-text("重置")'

    # ========== 表格 ==========
    TABLE = ".el-table"
    TABLE_LOADING = ".el-table__body .el-loading-mask"
    TABLE_ROWS = ".el-table__body tr"
    TABLE_EMPTY = ".el-table__empty-text"

    # ========== 表格列 ==========
    TASK_NAME_COLUMN = ".el-table__body tr td:nth-child(2)"
    STATUS_COLUMN = ".el-table__body tr td:nth-child(3)"
    STATUS_DOT = ".w-3.h-3.rounded-full"
    STATUS_TAG = ".status-tag"
    CASE_COLUMN = ".el-table__body tr td:nth-child(4)"
    NODE_COLUMN = ".el-table__body tr td:nth-child(5)"
    PROGRESS_COLUMN = ".el-table__body tr td:nth-child(6)"
    PROGRESS_BAR = ".el-progress"
    CREATE_TIME_COLUMN = ".el-table__body tr td:nth-child(7)"
    ACTIONS_COLUMN = ".el-table__body tr td:nth-child(8)"

    # ========== 行操作按钮 ==========
    START_BUTTON = 'button:has-text("启动")'
    STOP_BUTTON = 'button:has-text("停止")'
    DETAIL_LINK = 'a:has-text("详情")'
    MORE_ACTIONS_BUTTON = "button:has-text('...')"
    VIEW_LOGS_ITEM = '.el-dropdown-menu__item:has-text("查看日志")'
    VIEW_METRICS_ITEM = '.el-dropdown-menu__item:has-text("性能数据")'
    DELETE_ITEM = '.el-dropdown-menu__item:has-text("删除")'

    # ========== 复选框 ==========
    ROW_CHECKBOX = ".el-table__body tr .el-checkbox__input"
    SELECT_ALL_CHECKBOX = ".el-table__header th:first-child .el-checkbox__input"

    # ========== 分页 ==========
    PAGINATION = ".el-pagination"
    PAGINATION_TOTAL = ".el-pagination__total"

    # ========== 对话框 ==========
    CREATE_DIALOG = '.el-dialog:has-text("创建任务")'
    LOGS_DIALOG = '.el-dialog:has-text("任务日志")'
    METRICS_DIALOG = '.el-dialog:has-text("性能数据")'

    # ========== 确认对话框 ==========
    CONFIRM_DIALOG = ".el-message-box"
    CONFIRM_DELETE_BUTTON = 'button:has-text("确定")'
    CANCEL_BUTTON = 'button:has-text("取消")'

    # ========== 空状态 ==========
    EMPTY_STATE = ".el-table__empty-text"

    # ========== 状态选项 ==========
    STATUS_OPTION_ALL = 'el-option[value=""]'
    STATUS_OPTION_PENDING = 'el-option[value="pending"]'
    STATUS_OPTION_RUNNING = 'el-option[value="running"]'
    STATUS_OPTION_COMPLETED = 'el-option[value="completed"]'
    STATUS_OPTION_FAILED = 'el-option[value="failed"]'


class TasksListPage(BasePage):
    """
    任务列表页面对象

    URL: /tasks
    """

    URL = "/tasks"

    def __init__(self, page: Page, timeout: int = 30000):
        super().__init__(page, timeout)
        self._selectors = TasksListSelectors()

    def goto(self, wait_until: str = "networkidle"):
        """导航到任务列表页"""
        super().goto(self.URL, wait_until)

    # ========== 搜索过滤操作 ==========

    def search(self, query: str):
        """
        搜索任务

        Args:
            query: 搜索关键词
        """
        self.fill(self.selectors.SEARCH_INPUT, query)
        self.click(self.selectors.SEARCH_BUTTON)
        self.wait.for_navigation()

    def reset_search(self):
        """重置搜索"""
        self.click(self.selectors.RESET_BUTTON)
        self.wait.for_navigation()

    def filter_by_status(self, status: str):
        """
        按状态筛选

        Args:
            status: "" 全部, "pending" 待执行, "running" 运行中, "completed" 已完成, "failed" 失败
        """
        self.click(self.selectors.STATUS_FILTER)
        self.wait.for_visible('.el-select-dropdown', timeout=5000)
        if status == "":
            # Click by index for 全部
            self._click_dropdown_item_by_index(0)
        elif status == "pending":
            # Click by index since el-option values are not set
            self._click_dropdown_item_by_index(1)
        elif status == "running":
            self._click_dropdown_item_by_index(2)
        elif status == "completed":
            self._click_dropdown_item_by_index(3)
        elif status == "failed":
            self._click_dropdown_item_by_index(4)

    def _click_dropdown_item_by_index(self, index: int):
        """通过索引点击下拉选项"""
        items = self.page.query_selector_all('.el-select-dropdown__item')
        if len(items) > index:
            items[index].click()

    # ========== 表格操作 ==========

    def wait_for_table_loaded(self, timeout: Optional[int] = None):
        """等待表格加载完成"""
        try:
            self.wait.for_hidden(self.selectors.TABLE_LOADING, timeout)
        except Exception:
            pass
        self.wait.for_element(self.selectors.TABLE_ROWS, timeout)

    def get_table_row_count(self) -> int:
        """获取表格行数"""
        self.wait_for_table_loaded()
        rows = self.page.query_selector_all(self.selectors.TABLE_ROWS)
        return len(rows) if rows else 0

    def get_task_names(self) -> List[str]:
        """获取所有任务名称"""
        self.wait_for_table_loaded()
        names = []
        rows = self.page.query_selector_all(self.selectors.TABLE_ROWS)
        for row in rows:
            try:
                cell = row.query_selector(self.selectors.TASK_NAME_COLUMN)
                if cell:
                    text = cell.inner_text()
                    names.append(text.split()[0])  # 取第一行作为名称
            except Exception:
                continue
        return names

    def get_task_status(self, task_name: str) -> Optional[str]:
        """
        获取指定任务的状态

        Args:
            task_name: 任务名称

        Returns:
            状态字符串: pending/running/completed/failed
        """
        self.wait_for_table_loaded()
        rows = self.page.query_selector_all(self.selectors.TABLE_ROWS)
        for row in rows:
            try:
                cell = row.query_selector(self.selectors.TASK_NAME_COLUMN)
                if cell and task_name in cell.inner_text():
                    status_tag = row.query_selector(self.selectors.STATUS_TAG)
                    if status_tag:
                        status_text = status_tag.inner_text().strip()
                        if "待执行" in status_text:
                            return "pending"
                        elif "运行中" in status_text:
                            return "running"
                        elif "已完成" in status_text:
                            return "completed"
                        elif "失败" in status_text:
                            return "failed"
            except Exception:
                continue
        return None

    def get_task_progress(self, task_name: str) -> Optional[int]:
        """
        获取指定任务的进度

        Args:
            task_name: 任务名称

        Returns:
            进度百分比 (0-100)
        """
        self.wait_for_table_loaded()
        rows = self.page.query_selector_all(self.selectors.TABLE_ROWS)
        for row in rows:
            try:
                cell = row.query_selector(self.selectors.TASK_NAME_COLUMN)
                if cell and task_name in cell.inner_text():
                    progress_bar = row.query_selector(self.selectors.PROGRESS_BAR)
                    if progress_bar:
                        style = progress_bar.get_attribute("style") or ""
                        # 解析 style 中的 width 百分比
                        import re
                        match = re.search(r'width:\s*(\d+)%', style)
                        if match:
                            return int(match.group(1))
            except Exception:
                continue
        return None

    def find_row_by_task_name(self, task_name: str) -> Optional[object]:
        """根据任务名称查找行"""
        self.wait_for_table_loaded()
        rows = self.page.query_selector_all(self.selectors.TABLE_ROWS)
        for row in rows:
            try:
                cell = row.query_selector(self.selectors.TASK_NAME_COLUMN)
                if cell and task_name in cell.inner_text():
                    return row
            except Exception:
                continue
        return None

    def get_tasks_by_status(self, status: str) -> List[Dict[str, str]]:
        """
        获取指定状态的所有任务

        Args:
            status: pending/running/completed/failed

        Returns:
            任务列表
        """
        tasks = []
        self.wait_for_table_loaded()
        rows = self.page.query_selector_all(self.selectors.TABLE_ROWS)

        for row in rows:
            try:
                name_cell = row.query_selector(self.selectors.TASK_NAME_COLUMN)
                status_tag = row.query_selector(self.selectors.STATUS_TAG)
                if name_cell and status_tag:
                    name = name_cell.inner_text().split()[0]
                    status_text = status_tag.inner_text().strip()
                    current_status = None
                    if "待执行" in status_text:
                        current_status = "pending"
                    elif "运行中" in status_text:
                        current_status = "running"
                    elif "已完成" in status_text:
                        current_status = "completed"
                    elif "失败" in status_text:
                        current_status = "failed"

                    if current_status == status:
                        tasks.append({"name": name, "status": status_text})
            except Exception:
                continue

        return tasks

    # ========== 选择操作 ==========

    def select_task(self, task_name: str):
        """选择指定任务的复选框"""
        row = self.find_row_by_task_name(task_name)
        if row:
            checkbox = row.query_selector(self.selectors.ROW_CHECKBOX)
            if checkbox:
                checkbox.click()

    def select_all_tasks(self):
        """选择所有任务"""
        checkbox = self.page.query_selector(self.selectors.SELECT_ALL_CHECKBOX)
        if checkbox:
            checkbox.click()

    def get_selected_count(self) -> int:
        """获取已选择的任务数量"""
        selected = self.page.query_selector_all(f"{self.selectors.TABLE_ROWS} .el-checkbox__input.is-checked")
        return len(selected)

    # ========== 操作按钮 ==========

    def click_batch_start(self):
        """点击批量启动按钮"""
        self.click(self.selectors.BATCH_START_BUTTON)

    def click_batch_stop(self):
        """点击批量停止按钮"""
        self.click(self.selectors.BATCH_STOP_BUTTON)

    def click_batch_delete(self):
        """点击批量删除按钮"""
        self.click(self.selectors.BATCH_DELETE_BUTTON)

    def click_create_task(self):
        """点击创建任务按钮"""
        self.click(self.selectors.CREATE_TASK_BUTTON)

    def click_start(self, task_name: str):
        """点击启动按钮"""
        row = self.find_row_by_task_name(task_name)
        if row:
            btn = row.query_selector(self.selectors.START_BUTTON)
            if btn:
                btn.click()
                return
        raise ValueError(f"Task not found or start button not available: {task_name}")

    def click_stop(self, task_name: str):
        """点击停止按钮"""
        row = self.find_row_by_task_name(task_name)
        if row:
            btn = row.query_selector(self.selectors.STOP_BUTTON)
            if btn:
                btn.click()
                return
        raise ValueError(f"Task not found or stop button not available: {task_name}")

    def click_detail(self, task_name: str):
        """点击详情链接"""
        row = self.find_row_by_task_name(task_name)
        if row:
            btn = row.query_selector('a:has-text("详情")')
            if btn:
                btn.click()
                return
        raise ValueError(f"Task not found or detail link not available: {task_name}")

    def click_view_logs(self, task_name: str):
        """点击查看日志"""
        row = self.find_row_by_task_name(task_name)
        if row:
            row.hover()
            more_btn = row.query_selector(self.selectors.MORE_ACTIONS_BUTTON)
            if more_btn:
                more_btn.click()
                self.wait.for_visible('.el-dropdown-menu')
                menu = self.page.query_selector('.el-dropdown-menu')
                items = menu.query_selector_all('.el-dropdown-menu__item')
                for item in items:
                    if "日志" in item.inner_text():
                        item.click()
                        return
        raise ValueError(f"Task not found or logs not available: {task_name}")

    def click_view_metrics(self, task_name: str):
        """点击查看性能数据"""
        row = self.find_row_by_task_name(task_name)
        if row:
            row.hover()
            more_btn = row.query_selector(self.selectors.MORE_ACTIONS_BUTTON)
            if more_btn:
                more_btn.click()
                self.wait.for_visible('.el-dropdown-menu')
                menu = self.page.query_selector('.el-dropdown-menu')
                items = menu.query_selector_all('.el-dropdown-menu__item')
                for item in items:
                    if "性能数据" in item.inner_text():
                        item.click()
                        return
        raise ValueError(f"Task not found or metrics not available: {task_name}")

    def click_delete(self, task_name: str):
        """点击删除"""
        row = self.find_row_by_task_name(task_name)
        if row:
            row.hover()
            more_btn = row.query_selector(self.selectors.MORE_ACTIONS_BUTTON)
            if more_btn:
                more_btn.click()
                self.wait.for_visible('.el-dropdown-menu')
                menu = self.page.query_selector('.el-dropdown-menu')
                items = menu.query_selector_all('.el-dropdown-menu__item')
                for item in items:
                    if "删除" in item.inner_text():
                        item.click()
                        return
        raise ValueError(f"Task not found or delete not available: {task_name}")

    # ========== 确认对话框 ==========

    def confirm_delete(self):
        """确认删除"""
        self.wait.for_visible(self.selectors.CONFIRM_DIALOG)
        self.click(self.selectors.CONFIRM_DELETE_BUTTON)

    def cancel_delete(self):
        """取消删除"""
        cancel_btn = self.page.query_selector(f"{self.selectors.CONFIRM_DIALOG} button:has-text('取消')")
        if cancel_btn:
            cancel_btn.click()

    # ========== 分页操作 ==========

    def is_pagination_visible(self) -> bool:
        """检查分页是否可见"""
        return self.is_visible(self.selectors.PAGINATION_TOTAL, timeout=3000)

    def get_total_count(self) -> int:
        """获取任务总数"""
        if self.is_visible(self.selectors.PAGINATION_TOTAL, timeout=3000):
            total_text = self.get_text(self.selectors.PAGINATION_TOTAL)
            import re
            match = re.search(r'\d+', total_text)
            return int(match.group()) if match else 0
        return self.get_table_row_count()

    # ========== 状态检查 ==========

    def is_empty(self) -> bool:
        """检查是否为空状态"""
        return self.is_visible(self.selectors.EMPTY_STATE, timeout=3000)

    def is_create_dialog_visible(self) -> bool:
        """检查创建对话框是否可见"""
        return self.is_visible(self.selectors.CREATE_DIALOG, timeout=3000)

    def is_logs_dialog_visible(self) -> bool:
        """检查日志对话框是否可见"""
        return self.is_visible(self.selectors.LOGS_DIALOG, timeout=3000)

    def is_metrics_dialog_visible(self) -> bool:
        """检查性能数据对话框是否可见"""
        return self.is_visible(self.selectors.METRICS_DIALOG, timeout=3000)

    def is_batch_start_enabled(self) -> bool:
        """检查批量启动按钮是否启用"""
        button = self.page.locator(self.selectors.BATCH_START_BUTTON)
        return not button.is_disabled()

    def is_batch_stop_enabled(self) -> bool:
        """检查批量停止按钮是否启用"""
        button = self.page.locator(self.selectors.BATCH_STOP_BUTTON)
        return not button.is_disabled()

    def is_batch_delete_enabled(self) -> bool:
        """检查批量删除按钮是否启用"""
        button = self.page.locator(self.selectors.BATCH_DELETE_BUTTON)
        return not button.is_disabled()

    # ========== 批量操作 ==========

    def batch_start_selected(self):
        """批量启动选中的任务"""
        self.click_batch_start()

    def batch_stop_selected(self):
        """批量停止选中的任务"""
        self.click_batch_stop()

    def batch_delete_selected(self):
        """批量删除选中的任务"""
        self.click_batch_delete()
        self.confirm_delete()
