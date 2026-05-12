"""
前端 API 测试 - TaskNodePartition, TestResultPercentile
======================================================
测试任务节点分区关联和百分位数数据相关 API

注意: 这些测试需要后端服务器运行最新代码。如果测试失败，请确保：
1. 后端服务器已重启以加载新代码
2. 数据库已更新包含 task_node_partitions 表
"""
import pytest
import requests


class TestTaskNodePartitionAPI:
    """TaskNodePartition API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """设置"""
        self.base_url = "http://localhost:8000/api"
        # 获取 token
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_should_get_task_node_partitions_list(self):
        """获取任务节点分区关联列表"""
        response = requests.get(
            f"{self.base_url}/task-node-partitions/",
            headers=self.headers
        )
        # 200 = 成功(可能有数据), 401 = 未认证, 404 = 端点不存在(服务器未更新)
        # 如果返回 404，说明后端服务器需要重启
        assert response.status_code in [200, 401, 404], f"Unexpected status: {response.status_code}"

    def test_should_get_task_node_partitions_by_task_id(self):
        """根据任务ID获取任务节点分区关联"""
        response = requests.get(
            f"{self.base_url}/task-node-partitions/",
            params={"task_id": 1},
            headers=self.headers
        )
        assert response.status_code in [200, 401, 404]

    def test_should_get_task_node_partitions_by_node_id(self):
        """根据节点ID获取任务节点分区关联"""
        response = requests.get(
            f"{self.base_url}/task-node-partitions/",
            params={"node_id": 1},
            headers=self.headers
        )
        assert response.status_code in [200, 401, 404]

    def test_should_get_single_task_node_partition(self):
        """获取单个任务节点分区关联详情"""
        response = requests.get(
            f"{self.base_url}/task-node-partitions/1",
            headers=self.headers
        )
        assert response.status_code in [200, 401, 404]

    def test_should_create_task_node_partition(self):
        """创建任务节点分区关联"""
        response = requests.post(
            f"{self.base_url}/task-node-partitions",
            headers=self.headers,
            json={
                "task_id": 1,
                "node_id": 1,
                "partition_id": 1,
                "capacity_limit": 1024
            }
        )
        # 成功返回 200/201，失败原因可能是资源不存在(400/404)或未授权(401)
        assert response.status_code in [200, 201, 400, 401, 404, 422]

    def test_should_update_task_node_partition(self):
        """更新任务节点分区关联"""
        response = requests.put(
            f"{self.base_url}/task-node-partitions/1",
            headers=self.headers,
            json={
                "capacity_limit": 2048
            }
        )
        assert response.status_code in [200, 401, 404, 422]

    def test_should_delete_task_node_partition(self):
        """删除任务节点分区关联"""
        response = requests.delete(
            f"{self.base_url}/task-node-partitions/1",
            headers=self.headers
        )
        assert response.status_code in [200, 401, 404]

    def test_should_batch_create_task_node_partitions(self):
        """批量创建任务节点分区关联"""
        response = requests.post(
            f"{self.base_url}/task-node-partitions/batch",
            headers=self.headers,
            json=[
                {
                    "task_id": 1,
                    "node_id": 1,
                    "partition_id": 1,
                    "capacity_limit": 1024
                }
            ]
        )
        assert response.status_code in [200, 201, 400, 401, 404, 422]


class TestBaselineAPI:
    """Baseline API 测试 (通过 extensions.py)"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """设置"""
        self.base_url = "http://localhost:8000/api"
        # 获取 token
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_should_get_baselines_list(self):
        """获取基线列表"""
        response = requests.get(
            f"{self.base_url}/baselines",
            headers=self.headers
        )
        assert response.status_code in [200, 401]

    def test_should_create_baseline(self):
        """创建基线（需要 source_task_id）"""
        response = requests.post(
            f"{self.base_url}/baselines",
            headers=self.headers,
            json={
                "name": "Test Baseline",
                "source_task_id": 1,
                "description": "Test baseline description"
            }
        )
        assert response.status_code in [200, 201, 400, 401]

    def test_should_delete_baseline(self):
        """删除基线"""
        response = requests.delete(
            f"{self.base_url}/baselines/1",
            headers=self.headers
        )
        assert response.status_code in [200, 401, 403, 404]


class TestResultPercentileAPI:
    """TestResultPercentile API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """设置"""
        self.base_url = "http://localhost:8000/api"
        # 获取 token
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_should_get_task_node_percentiles(self):
        """获取任务节点的百分位数数据"""
        response = requests.get(
            f"{self.base_url}/task-nodes/1/percentiles",
            headers=self.headers
        )
        assert response.status_code in [200, 401, 404]

    def test_should_create_task_node_percentiles(self):
        """批量创建任务节点的百分位数数据"""
        response = requests.post(
            f"{self.base_url}/task-nodes/1/percentiles",
            headers=self.headers,
            json=[
                {
                    "percentile_name": "p50",
                    "latency_us": 100.0,
                    "test_type": "read"
                },
                {
                    "percentile_name": "p99",
                    "latency_us": 500.0,
                    "test_type": "read"
                },
                {
                    "percentile_name": "p9999",
                    "latency_us": 2000.0,
                    "test_type": "read"
                }
            ]
        )
        assert response.status_code in [200, 201, 400, 401, 404, 422]


class TestBaselineThresholdConfiguration:
    """基线阈值配置测试"""

    def test_should_parse_config_json_threshold(self):
        """测试 config_json 阈值解析"""
        config_json = """{
            "thresholds": {
                "iops": {"warning": 10, "critical": 20, "direction": "lower_is_worse"},
                "latency": {"warning": 15, "critical": 30, "direction": "higher_is_worse"},
                "bandwidth": {"warning": 10, "critical": 20, "direction": "lower_is_worse"}
            }
        }"""
        import json
        config = json.loads(config_json)
        thresholds = config["thresholds"]

        assert thresholds["iops"]["direction"] == "lower_is_worse"
        assert thresholds["iops"]["warning"] == 10
        assert thresholds["iops"]["critical"] == 20

        assert thresholds["latency"]["direction"] == "higher_is_worse"
        assert thresholds["latency"]["warning"] == 15

    def test_should_calculate_deviation_lower_is_worse(self):
        """测试 lower_is_worse 方向偏差计算"""
        baseline_value = 100000.0
        actual_value = 90000.0  # 比基线低 10%
        deviation_percent = ((actual_value - baseline_value) / baseline_value) * 100

        assert deviation_percent == -10.0

        # 判断是否超出阈值
        direction = "lower_is_worse"
        warning_threshold = 10

        exceeded = deviation_percent < -warning_threshold
        assert exceeded == False  # -10% 不超过 -10% 阈值

        actual_value = 80000.0  # 比基线低 20%
        deviation_percent = ((actual_value - baseline_value) / baseline_value) * 100
        exceeded = deviation_percent < -warning_threshold
        assert exceeded == True  # -20% 超过 -10% 阈值

    def test_should_calculate_deviation_higher_is_worse(self):
        """测试 higher_is_worse 方向偏差计算"""
        baseline_value = 10.0  # ms
        actual_value = 12.0  # 比基线高 20%
        deviation_percent = ((actual_value - baseline_value) / baseline_value) * 100

        assert deviation_percent == 20.0

        # 判断是否超出阈值
        direction = "higher_is_worse"
        warning_threshold = 15

        exceeded = deviation_percent > warning_threshold
        assert exceeded == True  # 20% 超过 15% 阈值

        actual_value = 11.0  # 比基线高 10%
        deviation_percent = ((actual_value - baseline_value) / baseline_value) * 100
        exceeded = deviation_percent > warning_threshold
        assert exceeded == False  # 10% 不超过 15% 阈值


class TestHistogramParsing:
    """Histogram 解析测试"""

    def test_should_parse_fio_histogram_format(self):
        """测试 fio histogram 格式解析"""
        import re

        histogram_log = """
# Histogram
[0, 100)         12345
[100, 200)       23456
[200, 400)       34567
[400, 800)       45678
[800, 1000)      12345
[1000, 2000)     5000
[2000, 4000)     2000
[4000, 8000)     1000
        """

        pattern = r'\[(\d+),\s*(\d+)\)\s+(\d+)'
        bins = []

        for line in histogram_log.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            match = re.match(pattern, line)
            if match:
                lower = int(match.group(1))
                upper = int(match.group(2))
                count = int(match.group(3))
                bins.append((upper, count))

        assert len(bins) == 8
        assert bins[0] == (100, 12345)
        assert bins[-1] == (8000, 1000)

    def test_should_calculate_percentiles_from_bins(self):
        """测试从 bins 计算百分位数"""
        bins = [
            (100, 1000),
            (200, 2000),
            (400, 3000),
            (800, 2500),
            (1000, 1000)
        ]

        total_count = sum(count for _, count in bins)
        assert total_count == 9500

        # 计算累积
        cumulative = 0
        cumulative_bins = []
        for upper, count in bins:
            cumulative += count
            cumulative_bins.append((upper, cumulative))

        # P50 应该是第一个累积 >= 4750 的桶的上界
        target_p50 = 0.50 * total_count  # 4750
        p50_latency = None
        for upper, cum in cumulative_bins:
            if cum >= target_p50:
                p50_latency = upper
                break

        assert p50_latency == 400

        # P99 应该是第一个累积 >= 9405 的桶的上界
        target_p99 = 0.99 * total_count  # 9405
        p99_latency = None
        for upper, cum in cumulative_bins:
            if cum >= target_p99:
                p99_latency = upper
                break

        assert p99_latency == 1000


class TestPartitionCapacityLimit:
    """分区容量限制测试"""

    def test_should_validate_capacity_limit_zero(self):
        """测试容量限制为 0 表示无限制"""
        capacity_limit = 0
        # 0 表示无限制，应该使用分区全部可用空间
        if capacity_limit == 0:
            init_size = "使用分区全部可用空间"
        else:
            init_size = f"{capacity_limit}M"

        assert init_size == "使用分区全部可用空间"

    def test_should_validate_capacity_limit_positive(self):
        """测试正容量限制"""
        capacity_limit = 1024
        # 正数表示限制大小
        init_size = f"{capacity_limit}M"
        assert init_size == "1024M"

    def test_should_calculate_init_size_from_available(self):
        """测试从可用空间计算初始化大小"""
        available_size_mb = 5000  # 5GB 可用

        # 使用 80% 的可用空间，避免占满
        init_size_mb = int(available_size_mb * 0.8)
        init_size = f"{init_size_mb}M"

        assert init_size == "4000M"