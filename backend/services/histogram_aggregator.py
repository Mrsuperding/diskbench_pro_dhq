"""
P99/P9999 Histogram 聚合服务
===========================
从 fio 的 hist_clat.log 文件中收集 histogram 数据，聚合 bin 并计算百分位数。

FIO histogram 格式：
- 每行: latency_bucket count
- latency_bucket 是微秒级别的桶边界
- count 是该桶内的操作数

计算方法：
1. 收集所有节点的 histogram 数据
2. 聚合所有 bin 的 count
3. 计算累积分布
4. 提取 P50, P90, P95, P99, P999, P9999
"""
import re
import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from sqlalchemy.orm import Session
from core.database import SessionLocal
from models.task import Task, TaskNode, TaskLog
from models.task_node_partition import TestResultPercentile
from services.ssh_service import SSHService


class HistogramAggregator:
    """
    Histogram 聚合器

    从 fio 的 hist_clat.log 收集延迟直方图数据，计算百分位数。
    """

    # 百分位数定义
    PERCENTILES = [50, 90, 95, 99, 999, 9999]

    def __init__(self, socket_manager):
        self.socket_manager = socket_manager

    async def collect_and_aggregate(
        self,
        task_id: int,
        task_node_id: int,
        ssh_service: SSHService,
        hist_clat_log_path: str = "/tmp/fio_hist_clat.log"
    ) -> Dict[str, float]:
        """
        收集并聚合 histogram 数据

        Args:
            task_id: 任务ID
            task_node_id: 任务节点ID
            ssh_service: SSH 服务实例
            hist_clat_log_path: 远端 hist_clat.log 文件路径

        Returns:
            Dict[percentile_name, latency_us]: 百分位数结果
        """
        db = SessionLocal()

        try:
            # 读取 hist_clat.log 文件
            result = await ssh_service.execute_command(
                f"cat {hist_clat_log_path}",
                timeout=30
            )

            if not result.get("success"):
                await self._log_warning(
                    db, task_id,
                    f"读取 hist_clat.log 失败: {result.get('stderr', '')}"
                )
                return {}

            log_content = result.get("stdout", "")
            if not log_content:
                await self._log_warning(
                    db, task_id,
                    "hist_clat.log 文件为空"
                )
                return {}

            # 解析 histogram 数据
            bins = self._parse_histogram(log_content)
            if not bins:
                await self._log_warning(
                    db, task_id,
                    "hist_clat.log 解析失败，无有效数据"
                )
                return {}

            # 计算百分位数
            percentiles = self._calculate_percentiles(bins)

            # 存储到数据库
            await self._store_percentiles(db, task_node_id, percentiles)

            await self._log_info(
                db, task_id,
                f"节点 {task_node_id} Histogram 聚合完成: "
                f"P99={percentiles.get('p99', 0):.2f}us, "
                f"P9999={percentiles.get('p9999', 0):.2f}us"
            )

            return percentiles

        except Exception as e:
            await self._log_error(
                db, task_id,
                f"Histogram 聚合异常: {e!s}"
            )
            return {}

        finally:
            db.close()

    def _parse_histogram(self, content: str) -> List[Tuple[float, int]]:
        """
        解析 fio histogram 输出

        格式示例:
        [0, 100)         12345
        [100, 200)       23456
        [200, 400)       34567
        ...

        Returns:
            List[(bucket_upper_us, count)]: 桶上界和计数
        """
        bins = []
        # 匹配形如 "[0, 100)" 或 "[0, 100]" 的行
        pattern = r'\[(\d+),\s*(\d+)\)\s+(\d+)'

        for line in content.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            match = re.match(pattern, line)
            if match:
                lower = int(match.group(1))
                upper = int(match.group(2))
                count = int(match.group(3))

                # 使用桶的上界作为键
                bins.append((upper, count))

        # 按上界排序
        bins.sort(key=lambda x: x[0])
        return bins

    def _calculate_percentiles(self, bins: List[Tuple[float, int]]) -> Dict[str, float]:
        """
        从 histogram bins 计算百分位数

        Args:
            bins: List[(upper_us, count)], 按 upper_us 排序

        Returns:
            Dict[percentile_name, latency_us]
        """
        if not bins:
            return {}

        # 计算总操作数
        total_count = sum(count for _, count in bins)
        if total_count == 0:
            return {}

        # 计算累积计数
        cumulative = 0
        cumulative_bins = []
        for upper, count in bins:
            cumulative += count
            cumulative_bins.append((upper, cumulative))

        # 提取每个百分位数
        result = {}
        for p in self.PERCENTILES:
            target_count = (p / 10000.0) * total_count  # p9999 = p/10000

            # 找到第一个累积计数 >= target_count 的桶
            latency_us = None
            for upper, cum in cumulative_bins:
                if cum >= target_count:
                    latency_us = upper
                    break

            # 如果没找到，用最后一个桶
            if latency_us is None:
                latency_us = cumulative_bins[-1][0] if cumulative_bins else 0

            result[f"p{p}"] = latency_us

        return result

    async def _store_percentiles(
        self,
        db: Session,
        task_node_id: int,
        percentiles: Dict[str, float]
    ):
        """存储百分位数到数据库"""
        for name, latency_us in percentiles.items():
            percentile = TestResultPercentile(
                task_node_id=task_node_id,
                percentile_name=name,
                latency_us=latency_us,
                test_type="read"  # 可以根据实际情况区分 read/write
            )
            db.add(percentile)

        db.commit()

    async def collect_from_all_nodes(
        self,
        task_id: int,
        task_nodes: List[TaskNode]
    ) -> Dict[int, Dict[str, float]]:
        """
        从所有节点收集并聚合 histogram

        Args:
            task_id: 任务ID
            task_nodes: 任务节点列表

        Returns:
            Dict[task_node_id, percentiles]
        """
        results = {}

        # 并发从所有节点收集
        coros = []
        for tn in task_nodes:
            if tn.node and tn.status == "completed":
                coro = self._collect_from_node(task_id, tn)
                coros.append(coro)

        node_results = await asyncio.gather(*coros, return_exceptions=True)

        for tn, result in zip(task_nodes, node_results):
            if isinstance(result, Exception):
                results[tn.id] = {}
            else:
                results[tn.id] = result

        return results

    async def _collect_from_node(
        self,
        task_id: int,
        task_node: TaskNode
    ) -> Dict[str, float]:
        """
        从单个节点收集 histogram

        Returns:
            Dict[percentile_name, latency_us]
        """
        db = SessionLocal()
        ssh_service: Optional[SSHService] = None

        try:
            node = task_node.node
            if not node:
                return {}

            ssh_service = SSHService()
            ok = await ssh_service.connect(
                host=node.host,
                port=node.port,
                username=node.username,
                password=node.password,
                private_key=node.private_key,
            )

            if not ok:
                return {}

            # fio 默认的 hist_clat 日志路径
            hist_path = f"/tmp/fio_hist_clat_{task_id}_{task_node.id}.log"

            return await self.collect_and_aggregate(
                task_id,
                task_node.id,
                ssh_service,
                hist_path
            )

        except Exception as e:
            await self._log_error(
                db, task_id,
                f"从节点 {task_node.node.node_name if task_node.node else task_node.id} "
                f"收集 histogram 失败: {e!s}"
            )
            return {}

        finally:
            if ssh_service:
                ssh_service.close()
            db.close()

    async def _log_info(self, db: Session, task_id: int, msg: str):
        await self._add_log(db, task_id, "info", msg)

    async def _log_warning(self, db: Session, task_id: int, msg: str):
        await self._add_log(db, task_id, "warning", msg)

    async def _log_error(self, db: Session, task_id: int, msg: str):
        await self._add_log(db, task_id, "error", msg)

    async def _add_log(self, db: Session, task_id: int, level: str, message: str):
        entry = TaskLog(task_id=task_id, log_level=level, message=message, source="histogram_aggregator")
        db.add(entry)
        db.commit()
        try:
            await self.socket_manager.broadcast_to_task(
                str(task_id),
                "log_update",
                {
                    "level": level,
                    "message": message,
                    "source": "histogram_aggregator",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except Exception:
            pass