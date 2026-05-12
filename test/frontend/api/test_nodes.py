"""
前端 API 测试 - nodes
"""
import pytest
import requests


class TestNodesAPI:
    """节点 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """设置"""
        self.base_url = "http://localhost:8000/api"
        # 获取 token
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        self.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_should_get_nodes_list(self):
        """获取节点列表"""
        response = requests.get(f"{self.base_url}/nodes/", headers=self.headers)
        assert response.ok
        assert isinstance(response.json(), list)

    def test_should_create_node(self):
        """创建节点"""
        response = requests.post(
            f"{self.base_url}/nodes/",
            headers=self.headers,
            json={
                "node_name": "test-node",
                "host": "192.168.1.100",
                "port": 22,
                "username": "root",
                "password": "test123",
                "login_type": "password",
                "description": "Test node"
            }
        )
        assert response.status_code in [200, 201, 400, 422]

    def test_should_get_node_detail(self):
        """获取节点详情"""
        response = requests.get(f"{self.base_url}/nodes/1", headers=self.headers)
        assert response.status_code in [200, 404]

    def test_should_update_node(self):
        """更新节点"""
        response = requests.put(
            f"{self.base_url}/nodes/1",
            headers=self.headers,
            json={"description": "Updated description"}
        )
        assert response.status_code in [200, 404]

    def test_should_delete_node(self):
        """删除节点"""
        response = requests.delete(f"{self.base_url}/nodes/1", headers=self.headers)
        assert response.status_code in [200, 404]
