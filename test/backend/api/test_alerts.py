"""
告警管理接口测试

注意: alerts API 尚未实现，所有测试被跳过
"""
import pytest


class TestAlerts:
    """告警管理接口测试"""

    @pytest.mark.skip(reason="alerts API 尚未实现")
    def test_get_alert_rules(self, api_client):
        """获取告警规则列表"""
        response = api_client.get("/api/alerts/rules/")
        assert response.status_code == 200

    @pytest.mark.skip(reason="alerts API 尚未实现")
    def test_create_alert_rule(self, api_client):
        """创建告警规则"""
        rule_data = {
            "rule_name": "test-rule-001",
            "metric": "cpu_usage",
            "threshold": 90,
            "condition": "gt",
            "description": "CPU alert rule"
        }
        response = api_client.post("/api/alerts/rules/", json=rule_data)
        assert response.status_code in [200, 201, 400]

    @pytest.mark.skip(reason="alerts API 尚未实现")
    def test_get_alert_events(self, api_client):
        """获取告警事件"""
        response = api_client.get("/api/alerts/events/")
        assert response.status_code == 200
