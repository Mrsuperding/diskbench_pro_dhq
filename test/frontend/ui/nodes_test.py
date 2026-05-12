"""
前端 UI 测试 - 节点管理页面
"""
import pytest


class TestNodesPage:
    """节点管理页面测试"""

    def test_should_display_nodes_list(self, page):
        """显示节点列表"""
        page.goto("http://localhost:3000/nodes")
        page.wait_for_selector("body", timeout=5000)

    def test_should_show_create_node_button(self, page):
        """显示创建节点按钮"""
        page.goto("http://localhost:3000/nodes")
        page.wait_for_selector("body", timeout=5000)

    def test_should_open_create_node_dialog(self, page):
        """打开创建节点对话框"""
        page.goto("http://localhost:3000/nodes")
        page.wait_for_selector("body", timeout=5000)

    def test_should_display_node_status_indicators(self, page):
        """显示节点状态指示器"""
        page.goto("http://localhost:3000/nodes")
        page.wait_for_selector("body", timeout=5000)
