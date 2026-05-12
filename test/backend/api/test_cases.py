"""
用例管理接口测试
"""
import pytest


class TestCases:
    """用例管理接口测试"""

    def test_get_cases(self, api_client):
        """获取用例列表"""
        response = api_client.get("/api/cases/")
        assert response.status_code == 200

    def test_create_case(self, api_client):
        """创建测试用例"""
        case_data = {
            "case_name": "test-case-001",
            "description": "Test case description"
        }
        response = api_client.post("/api/cases/", json=case_data)
        assert response.status_code in [200, 201, 400]
