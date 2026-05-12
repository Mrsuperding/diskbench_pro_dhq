"""
Task Form Page - 创建任务表单页面对象
=====================================
提供创建任务对话框的元素定位器和操作方法
"""
from typing import Optional, List
from playwright.sync_api import Page
from page_objects.base.base_page import BasePage


class TaskFormSelectors:
    """创建任务表单选择器"""

    # ========== 对话框 ==========
    DIALOG = '.el-dialog'
    DIALOG_TITLE = '.el-dialog__header'
    CLOSE_BUTTON = '.el-dialog__close'

    # ========== 基本信息 ==========
    TASK_NAME_INPUT = 'input[placeholder="请输入任务名称"]'
    CASE_SELECT = '.el-select:has(input[placeholder="请选择测试用例"])'
    NODE_SELECT = '.el-select:has(input[placeholder="请选择目标节点"])'
    TEST_PATH_INPUT = 'input[placeholder*="测试路径"]'
    CONCURRENCY_INPUT = '.el-input-number input'


class TaskFormPage(BasePage):
    """
    创建任务表单页面对象
    """

    def __init__(self, page: Page, timeout: int = 30000):
        super().__init__(page, timeout)
        self._selectors = TaskFormSelectors()

    # ========== 对话框操作 ==========

    def is_dialog_visible(self, timeout: int = 5000) -> bool:
        """检查对话框是否可见"""
        return self.is_visible(self.selectors.DIALOG, timeout=timeout)

    def wait_for_dialog(self, timeout: Optional[int] = None):
        """等待对话框出现"""
        self.wait.for_visible(self.selectors.DIALOG, timeout)

    def cancel(self):
        """取消并关闭"""
        self.click('button:has-text("取消")')
        self.wait.for_hidden(self.selectors.DIALOG, timeout=5000)

    # ========== 基本信息 ==========

    def fill_task_name(self, name: str):
        """填写任务名称"""
        self.fill(self.selectors.TASK_NAME_INPUT, name)

    def get_task_name(self) -> str:
        """获取任务名称"""
        return self.get_value(self.selectors.TASK_NAME_INPUT)

    def select_case(self, case_name: str, timeout: int = 5000):
        """选择测试用例"""
        # 点击用例选择框
        self.click(self.selectors.CASE_SELECT)
        self.wait.for_visible('.el-select-dropdown', timeout=timeout)

        # 选择指定用例
        case_option = self.page.locator(f'.el-select-dropdown__item:has-text("{case_name}")').first
        if case_option.is_visible(timeout=2000):
            case_option.click()
        else:
            # 如果没找到精确匹配，选择第一个
            first_option = self.page.locator('.el-select-dropdown__item').first
            if first_option.is_visible(timeout=2000):
                first_option.click()
            else:
                raise ValueError(f"Case not found: {case_name}")

    def select_nodes(self, node_names: List[str]):
        """选择目标节点（支持多选）"""
        for node_name in node_names:
            # 点击节点选择框
            self.click(self.selectors.NODE_SELECT)
            self.wait.for_visible('.el-select-dropdown', timeout=5000)

            # 选择指定节点
            node_option = self.page.locator(f'.el-select-dropdown__item:has-text("{node_name}")').first
            if node_option.is_visible(timeout=2000):
                node_option.click()
            else:
                # 选择第一个
                first = self.page.locator('.el-select-dropdown__item').first
                if first.is_visible(timeout=2000):
                    first.click()

    def fill_test_path(self, path: str):
        """填写测试路径"""
        self.fill(self.selectors.TEST_PATH_INPUT, path)

    def set_concurrency(self, value: int):
        """设置并发度"""
        # 点击增加按钮直到达到目标值
        increase_btn = self.selectors.CONCURRENCY_INPUT.replace('input', '.el-input-number__increase')
        decrease_btn = self.selectors.CONCURRENCY_INPUT.replace('input', '.el-input-number__decrease')

        # 先获取当前值
        current = self.get_concurrency()
        diff = value - current

        for _ in range(abs(diff)):
            if diff > 0:
                self.click(increase_btn)
            else:
                self.click(decrease_btn)
            self.wait.for_timeout(100)

    def get_concurrency(self) -> int:
        """获取并发度"""
        input_elem = self.page.query_selector(self.selectors.CONCURRENCY_INPUT)
        if input_elem:
            val = input_elem.get_attribute("value")
            return int(val) if val else 1
        return 1

    # ========== 提交 ==========

    def submit(self):
        """提交表单"""
        self.click('button:has-text("创建任务")')
        self.wait.for_timeout(1000)