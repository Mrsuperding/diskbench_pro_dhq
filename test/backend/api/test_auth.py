"""
认证接口测试
"""
import pytest


class TestAuth:
    """认证相关接口测试"""

    def test_login_success(self, client):
        """测试正常登录"""
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data

    def test_login_invalid_credentials(self, client):
        """测试错误密码"""
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong_password"}
        )
        assert response.status_code == 401

    def test_get_current_user(self, api_client):
        """测试获取当前用户"""
        response = api_client.get("/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert "username" in data

    def test_refresh_token(self, client):
        """测试刷新令牌"""
        # 先登录获取 tokens
        login_response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        tokens = login_response.json()
        refresh_token = tokens.get("refresh_token")

        # 使用 refresh_token 获取新的 access_token
        # 注意：/refresh 接口使用查询参数
        response = client.post(
            f"/api/auth/refresh?refresh_token={refresh_token}"
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
