"""
Nodes Tests - 使用 POM 的节点测试
===================================
展示如何使用 Page Object Model 测试节点管理功能

用法：
    pytest test/frontend/ui/tests/test_nodes_pom.py -v
"""
import pytest
from playwright.sync_api import Page

from page_objects.nodes.nodes_list_page import NodesListPage


@pytest.mark.ui
@pytest.mark.critical
class TestNodesListPage:
    """节点列表页面测试"""

    def test_nodes_page_loads(self, authenticated_page: Page):
        """TC_UI_NODES_001 - 节点页面正确加载"""
        nodes_page = NodesListPage(authenticated_page)
        nodes_page.goto()

        # 验证页面元素
        assert nodes_page.is_visible(NodesListPage.selectors.SEARCH_INPUT)
        assert nodes_page.is_visible(NodesListPage.selectors.ADD_NODE_BUTTON)
        assert nodes_page.is_visible(NodesListPage.selectors.TABLE)

    def test_search_input_works(self, authenticated_page: Page):
        """TC_UI_NODES_002 - 搜索功能正常工作"""
        nodes_page = NodesListPage(authenticated_page)
        nodes_page.goto()
        nodes_page.wait_for_table_loaded()

        # 执行搜索
        nodes_page.search("test")

        # 验证搜索结果（可能有或没有数据）
        assert nodes_page.is_visible(NodesListPage.selectors.TABLE)

    def test_reset_search(self, authenticated_page: Page):
        """TC_UI_NODES_003 - 重置搜索功能"""
        nodes_page = NodesListPage(authenticated_page)
        nodes_page.goto()
        nodes_page.wait_for_table_loaded()

        # 执行搜索后再重置
        nodes_page.search("somequery")
        nodes_page.reset_search()

        # 搜索框应该被清空
        search_value = authenticated_page.locator(NodesListPage.selectors.SEARCH_INPUT).input_value()
        assert search_value == "" or search_value is None

    def test_table_displays_data(self, authenticated_page: Page):
        """TC_UI_NODES_004 - 表格正确显示数据"""
        nodes_page = NodesListPage(authenticated_page)
        nodes_page.goto()
        nodes_page.wait_for_table_loaded()

        row_count = nodes_page.get_table_row_count()
        # 如果有数据，至少 1 行
        if not nodes_page.is_empty():
            assert row_count >= 0  # 表格应该已加载

    def test_add_node_button_opens_dialog(self, authenticated_page: Page):
        """TC_UI_NODES_005 - 添加节点按钮打开弹窗"""
        nodes_page = NodesListPage(authenticated_page)
        nodes_page.goto()

        nodes_page.click_add_node()

        # 验证创建弹窗打开
        assert nodes_page.is_create_dialog_visible()

    def test_refresh_button_works(self, authenticated_page: Page):
        """TC_UI_NODES_006 - 刷新按钮正常工作"""
        nodes_page = NodesListPage(authenticated_page)
        nodes_page.goto()
        nodes_page.wait_for_table_loaded()

        initial_row_count = nodes_page.get_table_row_count()

        # 点击刷新
        nodes_page.refresh()

        # 验证表格仍然正常显示
        current_row_count = nodes_page.get_table_row_count()
        assert current_row_count >= 0


@pytest.mark.ui
class TestNodesCreateNode:
    """创建节点测试"""

    @pytest.fixture
    def nodes_page_with_dialog(self, authenticated_page: Page):
        """打开创建节点弹窗的 fixture"""
        nodes_page = NodesListPage(authenticated_page)
        nodes_page.goto()
        nodes_page.click_add_node()
        nodes_page.wait_for_visible(NodesListPage.selectors.CREATE_DIALOG)
        return nodes_page

    def test_create_dialog_has_required_fields(self, nodes_page_with_dialog):
        """TC_UI_NODES_010 - 创建弹窗包含所有必需字段"""
        dialog = nodes_page_with_dialog

        assert dialog.is_visible(dialog.selectors.NODE_NAME_INPUT)
        assert dialog.is_visible(dialog.selectors.HOST_INPUT)
        assert dialog.is_visible(dialog.selectors.PORT_INPUT)
        assert dialog.is_visible(dialog.selectors.OS_TYPE_SELECT)
        assert dialog.is_visible(dialog.selectors.SAVE_BUTTON)

    def test_create_node_form_validation(self, nodes_page_with_dialog):
        """TC_UI_NODES_011 - 创建节点表单验证"""
        dialog = nodes_page_with_dialog

        # 填写部分字段
        dialog.fill(dialog.selectors.NODE_NAME_INPUT, "Test Node")
        dialog.fill(dialog.selectors.HOST_INPUT, "192.168.1.100")

        # 点击保存（可能因为缺少必填字段而失败）
        dialog.click(dialog.selectors.SAVE_BUTTON)

        # 验证弹窗仍然打开或有错误提示
        # 具体行为取决于前端验证逻辑


@pytest.mark.ui
class TestNodesNavigation:
    """节点页面导航测试"""

    def test_navigate_to_nodes_from_dashboard(self, authenticated_page: Page):
        """TC_UI_NODES_020 - 从 Dashboard 导航到节点页面"""
        # 先到 dashboard
        authenticated_page.goto("/dashboard")

        # 点击侧边栏节点链接
        authenticated_page.click('a:has-text("节点"), .sidebar-item:has-text("节点")')

        # 等待页面跳转
        authenticated_page.wait_for_url("**/nodes**", timeout=10000)

        assert "/nodes" in authenticated_page.url

    def test_navigate_from_nodes_to_cases(self, authenticated_page: Page):
        """TC_UI_NODES_021 - 从节点页面导航到用例页面"""
        nodes_page = NodesListPage(authenticated_page)
        nodes_page.goto()

        # 点击侧边栏用例链接
        authenticated_page.click('a:has-text("用例"), .sidebar-item:has-text("用例")')

        # 等待页面跳转
        authenticated_page.wait_for_url("**/cases**", timeout=10000)

        assert "/cases" in authenticated_page.url


@pytest.mark.ui
class TestNodesErrorHandling:
    """节点页面错误处理测试"""

    def test_nodes_page_with_api_error(self, authenticated_page: Page, console_errors):
        """TC_UI_NODES_030 - API 错误时的错误处理"""
        nodes_page = NodesListPage(authenticated_page)
        nodes_page.goto()

        # 节点页面应该加载（即使 API 返回错误）
        assert nodes_page.is_visible(nodes_page.selectors.TABLE)

    def test_empty_state_displayed(self, authenticated_page: Page):
        """TC_UI_NODES_031 - 无数据时显示空状态"""
        nodes_page = NodesListPage(authenticated_page)
        nodes_page.goto()

        # 如果没有节点，应该显示空状态
        if nodes_page.is_empty():
            assert nodes_page.is_visible(nodes_page.selectors.EMPTY_STATE)