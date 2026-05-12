"""
pytest configuration and fixtures for backend API tests
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# ============================================================================
# 路径配置 - 直接添加 backend 目录到 sys.path
# ============================================================================
# 直接使用绝对路径
backend_dir = r"D:\delvelop_project\ai_project\diskbench_pro\backend"
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# 导入 FastAPI 应用实例
from main import app


# ============================================================================
# Fixtures
# ============================================================================
@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def admin_token(client):
    """Get admin access token"""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    return response.json()["access_token"]


@pytest.fixture
def admin_headers(admin_token):
    """Admin authorization headers"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def api_client(client, admin_headers):
    """API client with admin authentication"""
    class APIClient:
        def __init__(self, client, headers):
            self.client = client
            self.headers = headers

        def get(self, url, **kwargs):
            return self.client.get(url, headers=self.headers, **kwargs)

        def post(self, url, json=None, **kwargs):
            return self.client.post(url, json=json, headers=self.headers, **kwargs)

        def put(self, url, json=None, **kwargs):
            return self.client.put(url, json=json, headers=self.headers, **kwargs)

        def delete(self, url, **kwargs):
            return self.client.delete(url, headers=self.headers, **kwargs)

    return APIClient(client, admin_headers)
