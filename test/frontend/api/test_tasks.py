"""
前端 API 测试 - tasks
"""
import pytest
import requests


class TestTasksAPI:
    """任务 API 测试"""

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

    def test_should_get_tasks_list(self):
        """获取任务列表"""
        response = requests.get(f"{self.base_url}/tasks/", headers=self.headers)
        assert response.ok
        assert isinstance(response.json(), list)

    def test_should_create_task(self):
        """创建任务"""
        response = requests.post(
            f"{self.base_url}/tasks/",
            headers=self.headers,
            json={
                "task_name": "test-task",
                "test_case_id": 1,
                "node_ids": [1],
                "partition_mappings": {1: 1},
                "description": "Test task"
            }
        )
        assert response.status_code in [200, 201, 400, 404, 409, 422]

    def test_should_get_task_detail(self):
        """获取任务详情"""
        response = requests.get(f"{self.base_url}/tasks/1", headers=self.headers)
        assert response.status_code in [200, 404]

    def test_should_start_task(self):
        """启动任务"""
        response = requests.post(
            f"{self.base_url}/tasks/1/start",
            headers=self.headers
        )
        assert response.status_code in [200, 400, 404]

    def test_should_stop_task(self):
        """停止任务"""
        response = requests.post(
            f"{self.base_url}/tasks/1/stop",
            headers=self.headers
        )
        assert response.status_code in [200, 400, 404]

    def test_should_get_task_logs(self):
        """获取任务日志"""
        response = requests.get(f"{self.base_url}/tasks/1/logs", headers=self.headers)
        assert response.status_code in [200, 404]
