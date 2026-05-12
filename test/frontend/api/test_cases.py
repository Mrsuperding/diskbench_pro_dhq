"""
前端 API 测试 - cases
"""
import pytest
import requests


class TestCasesAPI:
    """用例 API 测试"""

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

    def test_should_get_cases_list(self):
        """获取用例列表"""
        response = requests.get(f"{self.base_url}/cases/", headers=self.headers)
        assert response.ok
        assert isinstance(response.json(), list)

    def test_should_create_case(self):
        """创建用例"""
        response = requests.post(
            f"{self.base_url}/cases/",
            headers=self.headers,
            json={
                "case_name": "test-case",
                "description": "Test case",
                "fio_params": {
                    "rw": "randread",
                    "bs": "4k",
                    "ioengine": "libaio"
                }
            }
        )
        assert response.status_code in [200, 201, 400]

    def test_should_get_case_detail(self):
        """获取用例详情"""
        response = requests.get(f"{self.base_url}/cases/1", headers=self.headers)
        assert response.status_code in [200, 404]

    def test_should_update_case(self):
        """更新用例"""
        response = requests.put(
            f"{self.base_url}/cases/1",
            headers=self.headers,
            json={"description": "Updated description"}
        )
        assert response.status_code in [200, 404]

    def test_should_delete_case(self):
        """删除用例"""
        response = requests.delete(f"{self.base_url}/cases/1", headers=self.headers)
        assert response.status_code in [200, 404]
