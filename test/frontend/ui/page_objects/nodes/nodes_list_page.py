"""
Nodes List Page - 节点列表页面对象
===================================
提供节点管理页面的元素定位器和操作方法

用法：
    from page_objects.nodes.nodes_list_page import NodesListPage

    def test_nodes_list(authenticated_page):
        nodes_page = NodesListPage(authenticated_page)
        nodes_page.goto()
        count = nodes_page.get_table_row_count()
"""
from typing import Optional, List
from playwright.sync_api import Page
from page_objects.base.base_page import BasePage


class NodesListSelectors:
    """节点列表页面选择器"""

    # ========== 搜索和过滤 ==========
    SEARCH_INPUT = 'input[placeholder="搜索节点名称或主机地址"]'
    STATUS_FILTER = '.el-select[placeholder="状态筛选"]'
    SEARCH_BUTTON = 'button:has-text("搜索")'
    RESET_BUTTON = 'button:has-text("重置")'

    # ========== 操作按钮 ==========
    ADD_NODE_BUTTON = 'button:has-text("添加节点")'
    BATCH_TEST_BUTTON = 'button:has-text("批量测试")'
    BATCH_DELETE_BUTTON = 'button:has-text("批量删除")'
    REFRESH_BUTTON = 'button:has-text("刷新")'

    # ========== 表格 ==========
    TABLE = '.el-table'
    TABLE_ROWS = '.el-table__body tr'
    TABLE_LOADING = '.el-table__body .el-loading-mask'

    # ========== 表格列 ==========
    NODE_NAME_COLUMN = ".el-table__body tr td:nth-child(2)"
    HOST_COLUMN = ".el-table__body tr td:nth-child(3)"
    STATUS_COLUMN = ".el-table__body tr td:nth-child(4)"
    ACTIONS_COLUMN = ".el-table__body tr td:last-child"

    # ========== 行操作 ==========
    TEST_CONNECTION_BTN = 'button:has-text("测试连接")'
    EDIT_BTN = 'button:has-text("编辑")'
    DELETE_BTN = 'button:has-text("删除")'
    DETAIL_LINK = 'a:has-text("详情")'

    # ========== 状态指示器 ==========
    STATUS_DOT_ONLINE = '.status-dot.online, .el-tag--success'
    STATUS_DOT_OFFLINE = '.status-dot.offline, .el-tag--danger'

    # ========== 创建/编辑弹窗 ==========
    CREATE_DIALOG = '.el-dialog:has-text("添加节点")'
    EDIT_DIALOG = '.el-dialog:has-text("编辑节点")'
    NODE_NAME_INPUT = 'input[placeholder*="节点名称"]'
    HOST_INPUT = 'input[placeholder*="主机地址"]'
    PORT_INPUT = 'input[placeholder*="端口"]'
    OS_TYPE_SELECT = '.el-select[placeholder*="操作系统"]'
    SSH_USER_INPUT = 'input[placeholder*="SSH"]'
    SSH_PASSWORD_INPUT = 'input[placeholder*="密码"]'
    SAVE_BUTTON = 'button:has-text("确认")'
    CANCEL_BUTTON = 'button:has-text("取消")'

    # ========== 确认对话框 ==========
    CONFIRM_DIALOG = '.el-message-box'
    CONFIRM_DELETE_BTN = 'button:has-text("确定")'

    # ========== 空状态 ==========
    EMPTY_STATE = '.el-table__empty-text'
    NO_DATA_TEXT = "暂无数据"

    # ========== 分页 ==========
    PAGINATION = '.el-pagination'
    PAGINATION_TOTAL = '.el-pagination__total'


class NodesListPage(BasePage):
    """
    节点列表页面对象

    URL: /nodes
    """

    URL = "/nodes"

    def __init__(self, page: Page, timeout: int = 30000):
        super().__init__(page, timeout)
        self._selectors = NodesListSelectors()

    def goto(self, wait_until: str = "networkidle"):
        """导航到节点列表页"""
        super().goto(self.URL, wait_until)

    # ========== 搜索操作 ==========

    def search(self, query: str):
        """
        搜索节点

        Args:
            query: 搜索关键词（节点名称或主机地址）
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
            status: "online", "offline", 或 "all"
        """
        self.click(self.selectors.STATUS_FILTER)
        if status == "online":
            self.page.click('.el-select-dropdown__item:has-text("在线")')
        elif status == "offline":
            self.page.click('.el-select-dropdown__item:has-text("离线")')
        else:
            self.page.click('.el-select-dropdown__item:has-text("全部")')

    # ========== 表格操作 ==========

    def wait_for_table_loaded(self, timeout: Optional[int] = None):
        """等待表格加载完成"""
        # 等待 loading 消失
        try:
            self.wait.for_hidden(self.selectors.TABLE_LOADING, timeout)
        except Exception:
            pass
        # 等待表格行出现
        self.wait.for_element(self.selectors.TABLE_ROWS)

    def get_table_row_count(self) -> int:
        """获取表格行数"""
        self.wait_for_table_loaded()
        rows = self.page.query_selector_all(self.selectors.TABLE_ROWS)
        return len(rows) if rows else 0

    def get_node_names(self) -> List[str]:
        """获取所有节点名称"""
        self.wait_for_table_loaded()
        names = []
        rows = self.page.query_selector_all(self.selectors.TABLE_ROWS)
        for row in rows:
            cell = row.query_selector("td:nth-child(2)")
            if cell:
                names.append(cell.inner_text().strip())
        return names

    def get_node_status(self, node_name: str) -> Optional[str]:
        """
        获取指定节点的状态

        Args:
            node_name: 节点名称

        Returns:
            "online", "offline", 或 None
        """
        self.wait_for_table_loaded()
        rows = self.page.query_selector_all(self.selectors.TABLE_ROWS)
        for row in rows:
            cell = row.query_selector("td:nth-child(2)")
            if cell and node_name in cell.inner_text():
                status_cell = row.query_selector("td:nth-child(4)")
                if status_cell:
                    text = status_cell.inner_text().strip()
                    if "在线" in text or "online" in text.lower():
                        return "online"
                    elif "离线" in text or "offline" in text.lower():
                        return "offline"
        return None

    def find_row_by_node_name(self, node_name: str) -> Optional[object]:
        """根据节点名称查找行"""
        self.wait_for_table_loaded()
        rows = self.page.query_selector_all(self.selectors.TABLE_ROWS)
        for row in rows:
            cell = row.query_selector("td:nth-child(2)")
            if cell and node_name in cell.inner_text():
                return row
        return None

    # ========== 操作按钮 ==========

    def click_add_node(self):
        """点击添加节点按钮"""
        self.click(self.selectors.ADD_NODE_BUTTON)
        # 等待创建弹窗出现
        self.wait.for_visible(self.selectors.CREATE_DIALOG)

    def click_edit_node(self, node_name: str):
        """点击编辑节点按钮"""
        row = self.find_row_by_node_name(node_name)
        if row:
            row.hover()
            actions = row.query_selector_all("button")
            for action in actions:
                if "编辑" in action.inner_text():
                    action.click()
                    return
        raise ValueError(f"Node not found or edit button not available: {node_name}")

    def click_delete_node(self, node_name: str):
        """点击删除节点按钮"""
        row = self.find_row_by_node_name(node_name)
        if row:
            row.hover()
            actions = row.query_selector_all("button")
            for action in actions:
                if "删除" in action.inner_text():
                    action.click()
                    return
        raise ValueError(f"Node not found or delete button not available: {node_name}")

    def click_test_connection(self, node_name: str):
        """点击测试连接按钮"""
        row = self.find_row_by_node_name(node_name)
        if row:
            row.hover()
            actions = row.query_selector_all("button")
            for action in actions:
                if "测试连接" in action.inner_text():
                    action.click()
                    return
        raise ValueError(f"Node not found or test button not available: {node_name}")

    # ========== 创建/编辑弹窗操作 ==========

    def create_node(self, name: str, host: str, port: int = 22, os_type: str = "linux", ssh_user: str = "root", ssh_password: str = ""):
        """
        创建新节点

        Args:
            name: 节点名称
            host: 主机地址
            port: SSH 端口
            os_type: 操作系统类型 (linux/windows)
            ssh_user: SSH 用户名
            ssh_password: SSH 密码
        """
        # 打开创建弹窗
        self.click_add_node()

        # 填写表单
        self.wait.for_visible(self.selectors.NODE_NAME_INPUT)
        self.fill(self.selectors.NODE_NAME_INPUT, name)
        self.fill(self.selectors.HOST_INPUT, host)
        self.fill(self.selectors.PORT_INPUT, str(port))

        # 选择操作系统类型
        self.click(self.selectors.OS_TYPE_SELECT)
        self.page.wait_for_selector(".el-select-dropdown__item", state="visible")
        os_option = "Linux" if os_type.lower() == "linux" else "Windows"
        self.page.click(f".el-select-dropdown__item:has-text('{os_option}')")

        # 填写 SSH 凭证
        self.fill(self.selectors.SSH_USER_INPUT, ssh_user)
        self.fill(self.selectors.SSH_PASSWORD_INPUT, ssh_password)

        # 点击保存
        self.click(self.selectors.SAVE_BUTTON)

    def is_create_dialog_visible(self) -> bool:
        """检查创建弹窗是否可见"""
        return self.is_visible(self.selectors.CREATE_DIALOG)

    def is_edit_dialog_visible(self) -> bool:
        """检查编辑弹窗是否可见"""
        return self.is_visible(self.selectors.EDIT_DIALOG)

    def close_dialog(self):
        """关闭弹窗"""
        dialog = self.page.query_selector(".el-dialog:not([aria-hidden='true']):visible")
        if dialog:
            close_btn = dialog.query_selector(".el-dialog__headerbtn")
            if close_btn:
                close_btn.click()

    # ========== 确认对话框 ==========

    def confirm_delete(self):
        """确认删除"""
        self.wait.for_visible(self.selectors.CONFIRM_DIALOG)
        self.click(self.selectors.CONFIRM_DELETE_BTN)

    def cancel_delete(self):
        """取消删除"""
        cancel_btn = self.page.query_selector(f"{self.selectors.CONFIRM_DIALOG} button:has-text('取消')")
        if cancel_btn:
            cancel_btn.click()

    # ========== 状态检查 ==========

    def is_empty(self) -> bool:
        """检查是否为空状态（无数据）"""
        return self.is_visible(self.selectors.EMPTY_STATE, timeout=3000)

    def get_total_count(self) -> int:
        """获取节点总数"""
        if self.is_visible(self.selectors.PAGINATION_TOTAL, timeout=3000):
            total_text = self.get_text(self.selectors.PAGINATION_TOTAL)
            import re
            match = re.search(r'\d+', total_text)
            return int(match.group()) if match else 0
        return self.get_table_row_count()

    # ========== 刷新 ==========

    def refresh(self):
        """刷新节点列表"""
        self.click(self.selectors.REFRESH_BUTTON)
        self.wait_for_table_loaded()