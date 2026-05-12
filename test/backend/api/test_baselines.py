"""
性能基准接口测试
"""
import pytest


class TestBaselines:
    """性能基准接口测试"""

    def test_get_baselines(self, api_client):
        """获取基准列表"""
        response = api_client.get("/api/baselines/")
        assert response.status_code == 200

    def test_create_baseline(self, api_client):
        """创建性能基准"""
        baseline_data = {
            "source_task_id": 1,
            "name": "test-baseline-001",
            "description": "Test baseline"
        }
        response = api_client.post("/api/baselines/", json=baseline_data)
        assert response.status_code in [200, 201, 400]

    def test_compare_baseline(self, api_client):
        """对比性能数据"""
        response = api_client.get("/api/baselines/1/compare?task_id=2")
        assert response.status_code in [200, 404]
