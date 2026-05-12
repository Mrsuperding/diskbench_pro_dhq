"""
前端 API 测试 - auth
"""
import pytest


class TestAuthAPI:
    """认证 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """设置"""
        self.base_url = "http://localhost:8000/api"

    def test_should_login_successfully(self):
        """登录成功"""
        import requests
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert response.ok
        data = response.json()
        assert "access_token" in data

    def test_should_get_current_user_info(self):
        """获取当前用户信息"""
        import requests
        # 先登录获取 token
        login_response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        token = login_response.json().get("access_token")

        response = requests.get(
            f"{self.base_url}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.ok
        data = response.json()
        assert "username" in data

    def test_should_fail_with_wrong_password(self):
        """密码错误登录失败"""
        import requests
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": "admin", "password": "wrongpassword"}
        )
        assert not response.ok or response.status_code == 401

    def test_should_fail_with_nonexistent_user(self):
        """用户不存在登录失败"""
        import requests
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": "nonexistent", "password": "anypassword"}
        )
        assert not response.ok or response.status_code == 401
