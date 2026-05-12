"""
Schedules List Page - 定时调度页面对象
======================================
提供定时调度页面的元素定位器和操作方法

用法：
    from page_objects.schedules.schedules_list_page import SchedulesListPage

    def test_schedules_list(authenticated_page):
        schedules_page = SchedulesListPage(authenticated_page)
        schedules_page.goto()
        count = schedules_page.get_schedule_count()
"""
from typing import Optional, List, Dict
from playwright.sync_api import Page
from page_objects.base.base_page import BasePage


class SchedulesListSelectors:
    """定时调度页面选择器"""

    # ========== 页面标题 ==========
    PAGE_TITLE = "h1.page-title"
    PAGE_SUBTITLE = ".page-subtitle"

    # ========== 操作按钮 ==========
    CREATE_SCHEDULE_BUTTON = 'button:has-text("新建调度")'

    # ========== 表格 ==========
    TABLE = ".data-table"
    TABLE_ROWS = ".data-table tbody tr"

    # ========== 表格列 ==========
    NAME_COLUMN = "td:nth-child(1)"
    NAME_TITLE = ".cell-title"
    NAME_SUBTITLE = ".cell-sub"
    TRIGGER_COLUMN = "td:nth-child(2)"
    TRIGGER_TYPE_TAG = ".tag-info"
    TEMPLATE_TASK_COLUMN = "td:nth-child(3)"
    NEXT_RUN_COLUMN = "td:nth-child(4)"
    RECENT_COLUMN = "td:nth-child(5)"
    RECENT_STATUS_TAG = ".tag"
    RECENT_TIME = ".cell-sub"
    ENABLED_COLUMN = "td:nth-child(6)"
    ENABLE_SWITCH = ".el-switch"
    ACTIONS_COLUMN = "td:nth-child(7)"
    DELETE_BUTTON = 'button:has-text("删除")'

    # ========== 新建/编辑对话框 ==========
    DIALOG = ".el-dialog"
    DIALOG_TITLE = ".el-dialog__title"
    NAME_INPUT = 'input[placeholder*="名称"]'
    DESCRIPTION_INPUT = ".el-textarea__inner"
    TEMPLATE_TASK_INPUT = ".el-input-number input"
    TRIGGER_RADIO_GROUP = ".el-radio-group"
    ONCE_RADIO = '.el-radio-button:has-text("单次")'
    INTERVAL_RADIO = '.el-radio-button:has-text("间隔")'
    CRON_RADIO = '.el-radio-button:has-text("Cron")'
    INTERVAL_MINUTES_INPUT = ".el-input-number"
    CRON_EXPR_INPUT = 'input[placeholder="0 2 * * *"]'
    RUN_AT_PICKER = ".el-date-editor"
    SUBMIT_BUTTON = '.el-dialog button:has-text("创建"), .el-dialog button:has-text("保存")'
    CANCEL_BUTTON = '.el-dialog button:has-text("取消")'

    # ========== 确认对话框 ==========
    CONFIRM_DIALOG = ".el-message-box"
    CONFIRM_BUTTON = 'button:has-text("确定")'
    CANCEL_BUTTON_2 = 'button:has-text("取消")'

    # ========== 空状态 ==========
    EMPTY_STATE = ".text-muted:has-text('暂无调度')"
    EMPTY_TEXT = "暂无调度"


class SchedulesListPage(BasePage):
    """
    定时调度页面对象

    URL: /schedules
    """

    URL = "/schedules"

    def __init__(self, page: Page, timeout: int = 30000):
        super().__init__(page, timeout)
        self._selectors = SchedulesListSelectors()

    def goto(self, wait_until: str = "networkidle"):
        """导航到定时调度页"""
        super().goto(self.URL, wait_until)

    # ========== 表格操作 ==========

    def wait_for_table_loaded(self, timeout: Optional[int] = None):
        """等待表格加载完成"""
        self.wait.for_element(self.selectors.TABLE_ROWS, timeout)

    def get_schedule_count(self) -> int:
        """获取调度数量"""
        self.wait_for_table_loaded()
        rows = self.page.query_selector_all(self.selectors.TABLE_ROWS)
        # 过滤掉空状态行
        count = 0
        for row in rows:
            try:
                if row.query_selector(self.selectors.NAME_TITLE):
                    count += 1
            except Exception:
                continue
        return count

    def get_schedules(self) -> List[Dict[str, str]]:
        """
        获取所有调度信息

        Returns:
            调度列表
        """
        self.wait_for_table_loaded()
        schedules = []
        rows = self.page.query_selector_all(self.selectors.TABLE_ROWS)

        for row in rows:
            try:
                name_title = row.query_selector(self.selectors.NAME_TITLE)
                if not name_title:
                    continue

                name_subtitle = row.query_selector(self.selectors.NAME_SUBTITLE)
                trigger_tag = row.query_selector(self.selectors.TRIGGER_TYPE_TAG)
                template_task = row.query_selector(self.selectors.TEMPLATE_TASK_COLUMN)
                next_run = row.query_selector(self.selectors.NEXT_RUN_COLUMN)
                recent_tag = row.query_selector(self.selectors.RECENT_STATUS_TAG)

                schedules.append({
                    "name": name_title.inner_text().strip(),
                    "description": name_subtitle.inner_text().strip() if name_subtitle else "",
                    "trigger_type": trigger_tag.inner_text().strip() if trigger_tag else "",
                    "template_task": template_task.inner_text().strip() if template_task else "",
                    "next_run": next_run.inner_text().strip() if next_run else "",
                    "status": recent_tag.inner_text().strip() if recent_tag else "",
                })
            except Exception:
                continue

        return schedules

    def find_row_by_name(self, name: str) -> Optional[object]:
        """根据调度名称查找行"""
        self.wait_for_table_loaded()
        rows = self.page.query_selector_all(self.selectors.TABLE_ROWS)
        for row in rows:
            try:
                name_elem = row.query_selector(self.selectors.NAME_TITLE)
                if name_elem and name in name_elem.inner_text():
                    return row
            except Exception:
                continue
        return None

    def is_schedule_enabled(self, name: str) -> bool:
        """检查调度是否启用"""
        row = self.find_row_by_name(name)
        if row:
            switch = row.query_selector(self.selectors.ENABLE_SWITCH)
            if switch:
                classes = switch.get_attribute("class") or ""
                return "is-checked" in classes
        return False

    # ========== 操作按钮 ==========

    def click_create_schedule(self):
        """点击新建调度按钮"""
        self.click(self.selectors.CREATE_SCHEDULE_BUTTON)
        self.wait.for_visible(self.selectors.DIALOG)

    def click_delete(self, schedule_name: str):
        """点击删除按钮"""
        row = self.find_row_by_name(schedule_name)
        if row:
            btn = row.query_selector(self.selectors.DELETE_BUTTON)
            if btn:
                btn.click()

    def toggle_schedule(self, schedule_name: str, enabled: bool):
        """
        切换调度启用状态

        Args:
            schedule_name: 调度名称
            enabled: True 启用，False 禁用
        """
        row = self.find_row_by_name(schedule_name)
        if row:
            switch = row.query_selector(self.selectors.ENABLE_SWITCH)
            if switch:
                switch.click()

    # ========== 创建/编辑对话框 ==========

    def is_dialog_visible(self) -> bool:
        """检查对话框是否可见"""
        return self.is_visible(self.selectors.DIALOG, timeout=3000)

    def fill_schedule_form(
        self,
        name: str,
        description: str = "",
        template_task_id: int = 1,
        trigger_type: str = "interval",
        interval_minutes: int = 60,
        cron_expr: str = "",
    ):
        """
        填写调度表单

        Args:
            name: 调度名称
            description: 描述
            template_task_id: 模板任务 ID
            trigger_type: 触发类型 (once/interval/cron)
            interval_minutes: 间隔分钟数
            cron_expr: Cron 表达式
        """
        # 填写名称
        self.fill(self.selectors.NAME_INPUT, name)

        # 填写描述
        if description:
            desc_input = self.page.query_selector(self.selectors.DESCRIPTION_INPUT)
            if desc_input:
                desc_input.fill(description)

        # 填写模板任务 ID
        task_input = self.page.locator(self.selectors.TEMPLATE_TASK_INPUT).first
        task_input.fill(str(template_task_id))

        # 选择触发类型
        if trigger_type == "once":
            self.click(self.selectors.ONCE_RADIO)
        elif trigger_type == "interval":
            self.click(self.selectors.INTERVAL_RADIO)
            # 设置间隔
            interval_input = self.page.locator(self.selectors.INTERVAL_MINUTES_INPUT).first
            interval_input.fill(str(interval_minutes))
        elif trigger_type == "cron":
            self.click(self.selectors.CRON_RADIO)
            # 设置 Cron 表达式
            if cron_expr:
                self.fill(self.selectors.CRON_EXPR_INPUT, cron_expr)

    def submit_dialog(self):
        """提交对话框"""
        self.click(self.selectors.SUBMIT_BUTTON)

    def cancel_dialog(self):
        """取消对话框"""
        self.click(self.selectors.CANCEL_BUTTON)

    # ========== 确认对话框 ==========

    def confirm_delete(self):
        """确认删除"""
        self.wait.for_visible(self.selectors.CONFIRM_DIALOG)
        self.click(self.selectors.CONFIRM_BUTTON)

    def cancel_confirm(self):
        """取消确认"""
        self.click(self.selectors.CANCEL_BUTTON_2)

    # ========== 状态检查 ==========

    def is_empty(self) -> bool:
        """检查是否为空状态"""
        return self.is_visible(self.selectors.EMPTY_STATE, timeout=3000)

    # ========== 快捷操作 ==========

    def create_schedule(
        self,
        name: str,
        template_task_id: int = 1,
        trigger_type: str = "interval",
        interval_minutes: int = 60,
    ):
        """
        快速创建调度

        Args:
            name: 调度名称
            template_task_id: 模板任务 ID
            trigger_type: 触发类型
            interval_minutes: 间隔分钟数
        """
        self.click_create_schedule()
        self.fill_schedule_form(
            name=name,
            template_task_id=template_task_id,
            trigger_type=trigger_type,
            interval_minutes=interval_minutes,
        )
        self.submit_dialog()

    def delete_schedule(self, name: str):
        """
        删除调度

        Args:
            name: 调度名称
        """
        self.click_delete(name)
        self.confirm_delete()
