"""
Cases List Page - 用例列表页面对象
====================================
提供用例管理页面的元素定位器和操作方法

用法：
    from page_objects.cases.cases_list_page import CasesListPage

    def test_cases_list(authenticated_page):
        cases_page = CasesListPage(authenticated_page)
        cases_page.goto()
        count = cases_page.get_table_row_count()
"""
from typing import Optional, List
from playwright.sync_api import Page
from page_objects.base.base_page import BasePage


class CasesListSelectors:
    """用例列表页面选择器"""

    # ========== 页面标题 ==========
    PAGE_TITLE = "h1.page-title"
    PAGE_SUBTITLE = ".page-subtitle"

    # ========== 操作按钮 ==========
    USE_TEMPLATE_BUTTON = 'button:has-text("使用模板")'
    BATCH_DELETE_BUTTON = 'button:has-text("批量删除")'
    CREATE_CASE_BUTTON = 'button:has-text("创建用例")'

    # ========== 搜索和筛选 ==========
    SEARCH_INPUT = 'input[placeholder="搜索用例名称或描述"]'
    TYPE_FILTER = '.el-select[placeholder="类型筛选"]'
    SEARCH_BUTTON = 'button:has-text("搜索")'
    RESET_BUTTON = 'button:has-text("重置")'

    # ========== 表格 ==========
    TABLE = ".el-table"
    TABLE_LOADING = ".el-table__body .el-loading-mask"
    TABLE_ROWS = ".el-table__body tr"
    TABLE_EMPTY = ".el-table__empty-text"

    # ========== 表格列 ==========
    CASE_NAME_COLUMN = ".el-table__body tr td:nth-child(2)"
    TEST_TYPE_COLUMN = ".el-table__body tr td:nth-child(3)"
    BLOCK_SIZE_COLUMN = ".el-table__body tr td:nth-child(4)"
    IO_DEPTH_COLUMN = ".el-table__body tr td:nth-child(5)"
    TYPE_COLUMN = ".el-table__body tr td:nth-child(6)"
    CREATE_TIME_COLUMN = ".el-table__body tr td:nth-child(7)"
    ACTIONS_COLUMN = ".el-table__body tr td:nth-child(8)"

    # ========== 行操作按钮 ==========
    CLONE_BUTTON = 'button:has-text("克隆")'
    COMMAND_BUTTON = 'button:has-text("命令")'
    MORE_ACTIONS_BUTTON = "button:has-text('...')"
    EDIT_BUTTON = 'button:has-text("编辑")'
    TOGGLE_TEMPLATE_BUTTON = 'button:has-text("设为模板"), button:has-text("取消模板")'
    DETAIL_LINK = 'a:has-text("详情")'
    DELETE_BUTTON = 'button:has-text("删除")'

    # ========== 复选框 ==========
    ROW_CHECKBOX = ".el-table__body tr .el-checkbox__input"
    SELECT_ALL_CHECKBOX = ".el-table__header th:first-child .el-checkbox__input"

    # ========== 分页 ==========
    PAGINATION = ".el-pagination"
    PAGINATION_TOTAL = ".el-pagination__total"
    PAGINATION_PREV = ".el-pagination__prev"
    PAGINATION_NEXT = ".el-pagination__next"
    PAGE_SIZE_SELECT = ".el-pagination__sizes"

    # ========== 对话框 ==========
    CREATE_DIALOG = '.el-dialog:has-text("创建用例"), .el-dialog:has-text("编辑用例")'
    TEMPLATE_DIALOG = '.el-dialog:has-text("选择模板")'
    COMMAND_DIALOG = '.el-dialog:has-text("FIO 命令")'

    # ========== 确认对话框 ==========
    CONFIRM_DIALOG = ".el-message-box"
    CONFIRM_DELETE_BUTTON = 'button:has-text("确定")'
    CANCEL_BUTTON = 'button:has-text("取消")'

    # ========== 空状态 ==========
    EMPTY_STATE = ".el-table__empty-text"
    EMPTY_TEXT = "暂无数据"


class CasesListPage(BasePage):
    """
    用例列表页面对象

    URL: /cases
    """

    URL = "/cases"

    def __init__(self, page: Page, timeout: int = 30000):
        super().__init__(page, timeout)
        self._selectors = CasesListSelectors()

    def goto(self, wait_until: str = "networkidle"):
        """导航到用例列表页"""
        super().goto(self.URL, wait_until)

    # ========== 搜索过滤操作 ==========

    def search(self, query: str):
        """
        搜索用例

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

    def filter_by_type(self, filter_type: str = ""):
        """
        按类型筛选

        Args:
            filter_type: "" 全部, "false" 普通用例, "true" 模板用例
        """
        self.click(self.selectors.TYPE_FILTER)
        if filter_type == "":
            self.page.click('.el-option:has-text("全部")')
        elif filter_type == "false":
            self.page.click('.el-option:has-text("普通用例")')
        elif filter_type == "true":
            self.page.click('.el-option:has-text("模板用例")')

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

    def get_case_names(self) -> List[str]:
        """获取所有用例名称"""
        self.wait_for_table_loaded()
        names = []
        rows = self.page.query_selector_all(self.selectors.TABLE_ROWS)
        for row in rows:
            try:
                cell = row.query_selector(self.selectors.CASE_NAME_COLUMN)
                if cell:
                    text = cell.inner_text()
                    # 去除图标和多余空白
                    text = ' '.join(text.split())
                    names.append(text)
            except Exception:
                continue
        return names

    def get_test_type(self, case_name: str) -> Optional[str]:
        """
        获取指定用例的测试类型

        Args:
            case_name: 用例名称

        Returns:
            测试类型文本
        """
        self.wait_for_table_loaded()
        rows = self.page.query_selector_all(self.selectors.TABLE_ROWS)
        for row in rows:
            try:
                cell = row.query_selector(self.selectors.CASE_NAME_COLUMN)
                if cell and case_name in cell.inner_text():
                    type_cell = row.query_selector(self.selectors.TEST_TYPE_COLUMN)
                    if type_cell:
                        return type_cell.inner_text().strip()
            except Exception:
                continue
        return None

    def find_row_by_case_name(self, case_name: str) -> Optional[object]:
        """根据用例名称查找行"""
        self.wait_for_table_loaded()
        rows = self.page.query_selector_all(self.selectors.TABLE_ROWS)
        for row in rows:
            try:
                cell = row.query_selector(self.selectors.CASE_NAME_COLUMN)
                if cell and case_name in cell.inner_text():
                    return row
            except Exception:
                continue
        return None

    # ========== 选择操作 ==========

    def select_case(self, case_name: str):
        """选择指定用例的复选框"""
        row = self.find_row_by_case_name(case_name)
        if row:
            checkbox = row.query_selector(self.selectors.ROW_CHECKBOX)
            if checkbox:
                checkbox.click()

    def select_all_cases(self):
        """选择所有用例"""
        checkbox = self.page.query_selector(self.selectors.SELECT_ALL_CHECKBOX)
        if checkbox:
            checkbox.click()

    def get_selected_count(self) -> int:
        """获取已选择的用例数量"""
        selected = self.page.query_selector_all(f"{self.selectors.TABLE_ROWS} .el-checkbox__input.is-checked")
        return len(selected)

    # ========== 操作按钮 ==========

    def click_use_template(self):
        """点击使用模板按钮"""
        self.click(self.selectors.USE_TEMPLATE_BUTTON)

    def click_batch_delete(self):
        """点击批量删除按钮"""
        self.click(self.selectors.BATCH_DELETE_BUTTON)

    def click_create_case(self):
        """点击创建用例按钮"""
        self.click(self.selectors.CREATE_CASE_BUTTON)

    def click_clone(self, case_name: str):
        """点击克隆按钮"""
        row = self.find_row_by_case_name(case_name)
        if row:
            row.hover()
            buttons = row.query_selector_all("button")
            for btn in buttons:
                if "克隆" in btn.inner_text():
                    btn.click()
                    return
        raise ValueError(f"Case not found or clone button not available: {case_name}")

    def click_command(self, case_name: str):
        """点击命令按钮"""
        row = self.find_row_by_case_name(case_name)
        if row:
            row.hover()
            buttons = row.query_selector_all("button")
            for btn in buttons:
                if "命令" in btn.inner_text():
                    btn.click()
                    return
        raise ValueError(f"Case not found or command button not available: {case_name}")

    def click_edit(self, case_name: str):
        """点击编辑按钮"""
        row = self.find_row_by_case_name(case_name)
        if row:
            row.hover()
            # 展开下拉菜单
            more_btn = row.query_selector("button:has-text('...')")
            if more_btn:
                more_btn.click()
                self.wait.for_visible('.el-dropdown-menu')
                dropdown = self.page.query_selector('.el-dropdown-menu')
                items = dropdown.query_selector_all('.el-dropdown-menu__item')
                for item in items:
                    if "编辑" in item.inner_text():
                        item.click()
                        return
        raise ValueError(f"Case not found or edit not available: {case_name}")

    def click_delete(self, case_name: str):
        """点击删除按钮"""
        row = self.find_row_by_case_name(case_name)
        if row:
            row.hover()
            # 展开下拉菜单
            more_btn = row.query_selector("button:has-text('...')")
            if more_btn:
                more_btn.click()
                self.wait.for_visible('.el-dropdown-menu')
                dropdown = self.page.query_selector('.el-dropdown-menu')
                items = dropdown.query_selector_all('.el-dropdown-menu__item')
                for item in items:
                    if "删除" in item.inner_text():
                        item.click()
                        return
        raise ValueError(f"Case not found or delete not available: {case_name}")

    def click_detail(self, case_name: str):
        """点击详情链接"""
        row = self.find_row_by_case_name(case_name)
        if row:
            row.hover()
            more_btn = row.query_selector("button:has-text('...')")
            if more_btn:
                more_btn.click()
                self.wait.for_visible('.el-dropdown-menu')
                dropdown = self.page.query_selector('.el-dropdown-menu')
                items = dropdown.query_selector_all('.el-dropdown-menu__item')
                for item in items:
                    if "详情" in item.inner_text():
                        item.click()
                        return
        raise ValueError(f"Case not found or detail not available: {case_name}")

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
        """获取用例总数"""
        if self.is_visible(self.selectors.PAGINATION_TOTAL, timeout=3000):
            total_text = self.get_text(self.selectors.PAGINATION_TOTAL)
            import re
            match = re.search(r'\d+', total_text)
            return int(match.group()) if match else 0
        return self.get_table_row_count()

    def go_to_page(self, page: int):
        """跳转到指定页"""
        self.page.fill('.el-pagination input[type="number"]', str(page))
        self.page.press('.el-pagination input[type="number"]', 'Enter')

    def set_page_size(self, size: int):
        """设置每页条数"""
        self.click(self.selectors.PAGE_SIZE_SELECT)
        self.page.click(f'.el-select-dropdown__item:has-text("{size}")')

    # ========== 状态检查 ==========

    def is_empty(self) -> bool:
        """检查是否为空状态"""
        return self.is_visible(self.selectors.EMPTY_STATE, timeout=3000)

    def is_create_dialog_visible(self) -> bool:
        """检查创建对话框是否可见"""
        return self.is_visible(self.selectors.CREATE_DIALOG, timeout=3000)

    def is_template_dialog_visible(self) -> bool:
        """检查模板对话框是否可见"""
        return self.is_visible(self.selectors.TEMPLATE_DIALOG, timeout=3000)

    def is_command_dialog_visible(self) -> bool:
        """检查命令对话框是否可见"""
        return self.is_visible(self.selectors.COMMAND_DIALOG, timeout=3000)

    # ========== 获取对话框内容 ==========

    def get_command_content(self) -> str:
        """获取 FIO 命令内容"""
        if self.is_command_dialog_visible():
            return self.get_text(self.selectors.COMMAND_DIALOG)
        return ""

    # ========== 批量操作 ==========

    def batch_delete_selected(self):
        """批量删除选中的用例"""
        self.click_batch_delete()
        self.confirm_delete()

    def is_batch_delete_enabled(self) -> bool:
        """检查批量删除按钮是否启用"""
        button = self.page.locator(self.selectors.BATCH_DELETE_BUTTON)
        return not button.is_disabled()
