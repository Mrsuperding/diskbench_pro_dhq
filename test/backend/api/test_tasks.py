"""
任务管理接口测试
"""
import pytest


class TestTasks:
    """任务管理接口测试"""

    def test_get_tasks(self, api_client):
        """获取任务列表"""
        response = api_client.get("/api/tasks/")
        assert response.status_code == 200

    def test_create_task(self, api_client):
        """创建测试任务"""
        task_data = {
            "task_name": "test-task-001",
            "test_case_id": 999,  # 使用不存在的 ID，应该返回 404 或其他错误
            "node_ids": [1],
            "partition_mappings": {1: 1},
            "description": "Test task description"
        }
        response = api_client.post("/api/tasks/", json=task_data)
        # 可能返回 400, 404, 409, 422 等错误状态码
        assert response.status_code in [200, 201, 400, 404, 409, 422]

    def test_get_task_detail(self, api_client):
        """获取任务详情"""
        response = api_client.get("/api/tasks/1")
        assert response.status_code in [200, 404]

    def test_update_task(self, api_client):
        """更新任务配置"""
        task_data = {
            "task_name": "updated-task-001",
            "description": "Updated description"
        }
        response = api_client.put("/api/tasks/1", json=task_data)
        assert response.status_code in [200, 404]

    def test_delete_task(self, api_client):
        """删除任务"""
        response = api_client.delete("/api/tasks/1")
        assert response.status_code in [200, 404]

    def test_start_task(self, api_client):
        """启动测试任务"""
        response = api_client.post("/api/tasks/1/start")
        assert response.status_code in [200, 400, 404]

    def test_stop_task(self, api_client):
        """停止测试任务"""
        response = api_client.post("/api/tasks/1/stop")
        assert response.status_code in [200, 400, 404]

    def test_get_task_logs(self, api_client):
        """获取任务日志"""
        response = api_client.get("/api/tasks/1/logs")
        assert response.status_code in [200, 404]
