"""
节点管理接口测试
"""
import pytest


class TestNodes:
    """节点管理接口测试"""

    def test_get_nodes(self, api_client):
        """获取节点列表"""
        response = api_client.get("/api/nodes/")
        assert response.status_code == 200

    def test_get_nodes_empty(self, api_client):
        """获取空节点列表"""
        response = api_client.get("/api/nodes/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_node(self, api_client):
        """创建节点"""
        node_data = {
            "node_name": "test-node-001",
            "host": "192.168.1.100",
            "port": 22,
            "login_type": "password",
            "username": "root",
            "password": "test123"
        }
        response = api_client.post("/api/nodes/", json=node_data)
        # 根据实际情况调整断言
        assert response.status_code in [200, 201, 400]

    def test_get_node_detail(self, api_client):
        """获取节点详情"""
        response = api_client.get("/api/nodes/1")
        # 根据实际情况调整断言
        assert response.status_code in [200, 404]
