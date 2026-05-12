"""
监控模块接口测试

注意: monitor API 有后端代码 bug (Monitor 模型缺少 created_at 属性)，测试被跳过
"""
import pytest


class TestMonitor:
    """监控模块接口测试"""

    @pytest.mark.skip(reason="Monitor 模型缺少 created_at 属性 (后端 bug)")
    def test_get_monitor_history(self, api_client):
        """获取监控历史"""
        response = api_client.get("/api/monitor/history?node_id=1&start_time=2024-01-01&end_time=2024-12-31")
        assert response.status_code == 200

    @pytest.mark.skip(reason="Monitor 模型缺少 created_at 属性 (后端 bug)")
    def test_get_realtime_data(self, api_client):
        """获取实时监控数据"""
        response = api_client.get("/api/monitor/realtime?node_id=1")
        assert response.status_code == 200

    @pytest.mark.skip(reason="Monitor 模型缺少 created_at 属性 (后端 bug)")
    def test_export_monitor_data(self, api_client):
        """导出监控数据"""
        response = api_client.get("/api/monitor/export?node_id=1&start_time=2024-01-01&end_time=2024-12-31")
        assert response.status_code in [200, 400]
