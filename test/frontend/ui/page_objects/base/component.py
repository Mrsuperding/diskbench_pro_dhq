"""
Component Wrappers - 通用 UI 组件封装
=====================================
提供：
- Button: 按钮组件
- Input: 输入框组件
- Select: 下拉选择组件
- Table: 表格组件
- Dialog: 弹窗组件
- Pagination: 分页组件

用法：
    from page_objects.base.component import Button, Input, Table

    button = Button(page.locator('button.submit'))
    button.click()

    table = Table(page.locator('.el-table'))
    row_count = table.get_row_count()
"""
from typing import Optional, List, Dict, Any, Union
from playwright.sync_api import Locator, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


class Component:
    """基础组件封装"""

    def __init__(self, locator: Union[Locator, str]):
        if isinstance(locator, str):
            # 如果是字符串，选择器会在具体组件中处理
            self.locator = None
        else:
            self.locator = locator

    def click(self):
        """点击组件"""
        if self.locator:
            self.locator.click()

    def is_visible(self) -> bool:
        """检查组件是否可见"""
        return self.locator.is_visible() if self.locator else False

    def wait_for_visible(self, timeout: int = 30000):
        """等待组件可见"""
        if self.locator:
            self.locator.wait_for(state="visible", timeout=timeout)

    def wait_for_hidden(self, timeout: int = 30000):
        """等待组件隐藏"""
        if self.locator:
            self.locator.wait_for(state="hidden", timeout=timeout)

    def get_text(self) -> str:
        """获取组件文本"""
        return self.locator.inner_text() if self.locator else ""


class Button:
    """按钮组件封装"""

    def __init__(self, locator: Locator):
        self.locator = locator

    def click(self):
        """点击按钮"""
        self.locator.click()

    def is_disabled(self) -> bool:
        """检查按钮是否禁用"""
        return self.locator.get_attribute("disabled") is not None

    def is_visible(self) -> bool:
        """检查按钮是否可见"""
        return self.locator.is_visible()

    def get_text(self) -> str:
        """获取按钮文本"""
        return self.locator.inner_text()


class Input:
    """输入框组件封装"""

    def __init__(self, locator: Locator):
        self.locator = locator

    def fill(self, value: str):
        """填写输入框"""
        self.locator.fill(value)

    def clear(self):
        """清空输入框"""
        self.locator.fill("")

    def get_value(self) -> str:
        """获取输入框的值"""
        return self.locator.input_value()

    def press_enter(self):
        """按下回车键"""
        self.locator.press("Enter")

    def is_disabled(self) -> bool:
        """检查输入框是否禁用"""
        return self.locator.get_attribute("disabled") is not None


class Select:
    """下拉选择组件封装 (Element Plus)"""

    def __init__(self, page: Page, select_locator: str):
        self.page = page
        self.select_locator = select_locator

    def open(self):
        """打开下拉框"""
        self.page.click(self.select_locator)

    def select(self, value: str, by_label: bool = True):
        """
        选择选项

        Args:
            value: 选项值或文本
            by_label: True=按文本选择, False=按值选择
        """
        self.open()
        # 等待选项列表出现
        self.page.wait_for_selector(".el-select-dropdown__item", state="visible")
        if by_label:
            self.page.click(f".el-select-dropdown__item:has-text('{value}')")
        else:
            self.page.click(f".el-select-dropdown__item[data-value='{value}']")

    def get_selected_text(self) -> str:
        """获取已选选项的文本"""
        selected = self.page.locator(f"{self.select_locator} .el-input__inner").first
        return selected.input_value()


class Table:
    """
    表格组件封装 (Element Plus el-table)
    """

    def __init__(self, page: Page, table_locator: str = ".el-table"):
        self.page = page
        self.table_locator = table_locator

    def get_rows(self) -> List[Locator]:
        """获取所有数据行"""
        return self.page.query_selector_all(f"{self.table_locator} .el-table__body tr")

    def get_row_count(self) -> int:
        """获取行数"""
        return len(self.get_rows())

    def get_column_text(self, row: Locator, column_index: int) -> str:
        """获取指定单元格文本"""
        cell = row.query_selector(f"td:nth-child({column_index})")
        return cell.inner_text().strip() if cell else ""

    def get_column_values(self, column_index: int) -> List[str]:
        """获取列所有值"""
        values = []
        for row in self.get_rows():
            values.append(self.get_column_text(row, column_index))
        return values

    def find_row_by_column(self, column_index: int, text: str) -> Optional[Locator]:
        """根据列文本查找行"""
        for row in self.get_rows():
            if text in self.get_column_text(row, column_index):
                return row
        return None

    def click_row_action(self, row_text: str, column_index: int, action_text: str):
        """点击行中的操作按钮"""
        row = self.find_row_by_column(column_index, row_text)
        if row:
            row.hover()
            actions = row.query_selector_all("button")
            for action in actions:
                if action_text in action.inner_text():
                    action.click()
                    return

    def get_header_text(self, column_index: int) -> str:
        """获取表头文本"""
        header = self.page.query_selector(f"{self.table_locator} th:nth-child({column_index})")
        return header.inner_text().strip() if header else ""

    def sort_by_column(self, column_index: int, direction: str = "asc"):
        """
        按列排序

        Args:
            column_index: 列索引
            direction: 'asc' 或 'desc'
        """
        header = self.page.query_selector(f"{self.table_locator} th:nth-child({column_index})")
        if header:
            header.click()
            if direction == "desc":
                header.click()

    def select_row(self, row_index: int):
        """选择行（点击复选框）"""
        rows = self.get_rows()
        if 0 <= row_index < len(rows):
            checkbox = rows[row_index].query_selector(".el-checkbox__input")
            if checkbox:
                checkbox.click()

    def select_all_rows(self):
        """全选所有行"""
        header_checkbox = self.page.query_selector(f"{self.table_locator} .el-table__header .el-checkbox__input")
        if header_checkbox:
            header_checkbox.click()


class Dialog:
    """
    弹窗组件封装 (Element Plus el-dialog)
    """

    def __init__(self, page: Page, dialog_selector: str = ".el-dialog"):
        self.page = page
        self.dialog_selector = dialog_selector

    def is_open(self, timeout: int = 5000) -> bool:
        """检查弹窗是否打开"""
        try:
            self.page.wait_for_selector(self.dialog_selector, state="visible", timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            return False

    def is_closed(self, timeout: int = 5000) -> bool:
        """检查弹窗是否关闭"""
        try:
            self.page.wait_for_selector(self.dialog_selector, state="hidden", timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            return False

    def close(self):
        """关闭弹窗（点击关闭按钮或按 ESC）"""
        close_btn = f"{self.dialog_selector} .el-dialog__headerbtn"
        if self.page.is_visible(close_btn):
            self.page.click(close_btn)
        else:
            self.page.keyboard.press("Escape")

    def get_title(self) -> str:
        """获取弹窗标题"""
        title_elem = self.page.query_selector(f"{self.dialog_selector} .el-dialog__title")
        return title_elem.inner_text() if title_elem else ""

    def click_button(self, button_text: str):
        """点击弹窗内的按钮"""
        self.page.click(f"{self.dialog_selector} button:has-text('{button_text}')")

    def fill_field(self, label: str, value: str):
        """填写弹窗内的表单字段"""
        field = self.page.locator(f"{self.dialog_selector} .el-form-item:has-text('{label}')")
        input_elem = field.locator(".el-input input, .el-textarea textarea").first
        input_elem.fill(value)

    def get_field_value(self, label: str) -> str:
        """获取弹窗内字段的值"""
        field = self.page.locator(f"{self.dialog_selector} .el-form-item:has-text('{label}')")
        return field.locator("input").first.input_value()


class Pagination:
    """
    分页组件封装 (Element Plus el-pagination)
    """

    def __init__(self, page: Page, pagination_selector: str = ".el-pagination"):
        self.page = page
        self.pagination_selector = pagination_selector

    def get_total(self) -> int:
        """获取总条数"""
        total_elem = self.page.query_selector(f"{self.pagination_selector} .el-pagination__total")
        if total_elem:
            text = total_elem.inner_text()
            # 解析 "共 100 条" 或 "Total 100"
            import re
            match = re.search(r'\d+', text)
            return int(match.group()) if match else 0
        return 0

    def get_current_page(self) -> int:
        """获取当前页码"""
        current = self.page.query_selector(f"{self.pagination_selector} .el-pager .is-active")
        return int(current.inner_text()) if current else 1

    def go_to_page(self, page_num: int):
        """跳转到指定页"""
        input_elem = self.page.query_selector(f"{self.pagination_selector} .el-pagination__jump input")
        if input_elem:
            input_elem.fill(str(page_num))
            input_elem.press("Enter")

    def click_next(self):
        """点击下一页"""
        next_btn = self.page.query_selector(f"{self.pagination_selector} .el-pagination__next")
        if next_btn and not next_btn.get_attribute("disabled"):
            next_btn.click()

    def click_prev(self):
        """点击上一页"""
        prev_btn = self.page.query_selector(f"{self.pagination_selector} .el-pagination__prev")
        if prev_btn and not prev_btn.get_attribute("disabled"):
            prev_btn.click()


class Message:
    """
    消息提示封装 (Element Plus el-message)
    """

    def __init__(self, page: Page):
        self.page = page

    def get_text(self, message_type: str = "success", timeout: int = 5000) -> Optional[str]:
        """
        获取消息文本

        Args:
            message_type: success/error/warning/info
            timeout: 超时时间
        """
        selector = f".el-message--{message_type}"
        try:
            self.page.wait_for_selector(selector, state="visible", timeout=timeout)
            message_elem = self.page.query_selector(selector)
            return message_elem.inner_text() if message_elem else None
        except PlaywrightTimeoutError:
            return None

    def is_visible(self, message_type: str = "success", timeout: int = 5000) -> bool:
        """检查消息是否可见"""
        selector = f".el-message--{message_type}"
        return self.page.is_visible(selector)

    def wait_for_success(self, timeout: int = 5000) -> bool:
        """等待成功消息出现并返回文本"""
        text = self.get_text("success", timeout)
        return text is not None

    def wait_for_error(self, timeout: int = 5000) -> bool:
        """等待错误消息出现并返回文本"""
        text = self.get_text("error", timeout)
        return text is not None


class FormValidator:
    """
    表单验证辅助类
    """

    def __init__(self, page: Page, form_selector: str = ".el-form"):
        self.page = page
        self.form_selector = form_selector

    def get_field_error(self, label: str) -> Optional[str]:
        """获取字段验证错误信息"""
        field = self.page.locator(f"{self.form_selector} .el-form-item:has-text('{label}')")
        error_elem = field.locator(".el-form-item__error")
        if error_elem.is_visible():
            return error_elem.inner_text()
        return None

    def has_field_error(self, label: str) -> bool:
        """检查字段是否有验证错误"""
        return self.get_field_error(label) is not None

    def get_all_errors(self) -> Dict[str, str]:
        """获取所有字段错误"""
        errors = {}
        error_elems = self.page.query_selector_all(f"{self.form_selector} .el-form-item__error")
        for error in error_elems:
            # 找到对应的 label
            form_item = error.evaluate_handle("el => el.closest('.el-form-item')")
            if form_item:
                label_elem = form_item.query_selector(".el-form-item__label")
                if label_elem:
                    errors[label_elem.inner_text()] = error.inner_text()
        return errors