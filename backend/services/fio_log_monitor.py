import asyncio
import re
from datetime import datetime
from typing import Optional, Dict, List
from core.database import SessionLocal
from models.task import IOPerformanceData


class FIOLogMonitor:
    """
    FIO 日志实时监控服务

    功能：
    1. 定期（每秒）从远程节点读取 FIO 日志文件
    2. 解析并计算性能指标
    3. 存储到数据库
    4. 通过 WebSocket 推送到前端
    """

    def __init__(self, socket_manager):
        self.socket_manager = socket_manager
        self.active_monitors: Dict[str, asyncio.Task] = {}

    async def start_monitoring(
        self,
        task_id: int,
        task_node_id: int,
        ssh_service,
        log_prefix: str
    ):
        """
        启动日志监控

        Args:
            task_id: 任务ID
            task_node_id: 任务节点ID
            ssh_service: SSH 服务实例
            log_prefix: 日志文件前缀路径（如 /tmp/fio_123_456）
        """
        monitor_key = f"{task_id}_{task_node_id}"

        if monitor_key in self.active_monitors:
            return

        task = asyncio.create_task(
            self._monitor_loop(task_id, task_node_id, ssh_service, log_prefix)
        )
        self.active_monitors[monitor_key] = task

    async def stop_monitoring(self, task_id: int, task_node_id: int):
        """停止监控"""
        monitor_key = f"{task_id}_{task_node_id}"
        if monitor_key in self.active_monitors:
            self.active_monitors[monitor_key].cancel()
            try:
                await self.active_monitors[monitor_key]
            except asyncio.CancelledError:
                pass
            del self.active_monitors[monitor_key]

    async def _monitor_loop(
        self,
        task_id: int,
        task_node_id: int,
        ssh_service,
        log_prefix: str
    ):
        """
        监控循环：每秒读取并解析日志文件
        """
        db = SessionLocal()
        last_iops_pos = 0
        last_bw_pos = 0
        last_lat_pos = 0
        last_hist_pos = 0

        try:
            while True:
                current_iops = 0.0
                current_bw_kb = 0.0
                current_lat_ns = 0.0
                p99_us = 0.0
                p9999_us = 0.0
                max_lat_us = 0.0

                # 1. 读取 IOPS 日志
                iops_data = await self._read_log_incremental(
                    ssh_service, f"{log_prefix}_iops.log", last_iops_pos
                )
                if iops_data:
                    last_iops_pos = iops_data["new_pos"]
                    current_iops = iops_data["latest_value"]

                # 2. 读取带宽日志
                bw_data = await self._read_log_incremental(
                    ssh_service, f"{log_prefix}_bw.log", last_bw_pos
                )
                if bw_data:
                    last_bw_pos = bw_data["new_pos"]
                    current_bw_kb = bw_data["latest_value"] / 1024.0

                # 3. 读取延迟日志
                lat_data = await self._read_log_incremental(
                    ssh_service, f"{log_prefix}_lat.log", last_lat_pos
                )
                if lat_data:
                    last_lat_pos = lat_data["new_pos"]
                    current_lat_ns = lat_data["latest_value"]

                # 4. 读取直方图日志并计算 P99/P9999
                hist_data = await self._read_hist_incremental(
                    ssh_service, f"{log_prefix}_hist.log", last_hist_pos
                )
                if hist_data:
                    last_hist_pos = hist_data["new_pos"]
                    percentiles = self._calculate_percentiles_from_histogram(
                        hist_data["histograms"][-1] if hist_data["histograms"] else {}
                    )
                    p99_us = percentiles.get("p99", 0.0)
                    p9999_us = percentiles.get("p9999", 0.0)
                    max_lat_us = percentiles.get("max_lat_us", 0.0)

                # 5. 保存到数据库
                perf = IOPerformanceData(
                    task_node_id=task_node_id,
                    source="fio_realtime",
                    iops=current_iops,
                    bandwidth=current_bw_kb,
                    latency=current_lat_ns / 1_000_000.0,
                    p99_lat_us=p99_us,
                    p9999_lat_us=p9999_us,
                    max_lat_us=max_lat_us,
                )
                db.add(perf)
                db.commit()

                # 6. 通过 WebSocket 推送
                await self.socket_manager.broadcast_to_task(
                    str(task_id),
                    "realtime_performance",
                    {
                        "task_node_id": task_node_id,
                        "iops": current_iops,
                        "bw_mbs": current_bw_kb,
                        "lat_ms": current_lat_ns / 1_000_000.0,
                        "p99_us": p99_us,
                        "p9999_us": p9999_us,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

                await asyncio.sleep(1)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[FIOLogMonitor] Error: {e}")
        finally:
            db.close()

    async def _read_log_incremental(
        self,
        ssh_service,
        log_path: str,
        last_pos: int
    ) -> Optional[Dict]:
        """
        增量读取日志文件

        Returns:
            {
                "latest_value": float,
                "new_pos": int,
            }
        """
        result = await ssh_service.execute_command(
            f"cat {log_path} 2>/dev/null || true",
            timeout=10
        )

        if not result.get("success") or not result.get("stdout"):
            return None

        content = result["stdout"]
        lines = content.split("\n")

        if not lines:
            return None

        last_line = lines[-1].strip()
        if not last_line:
            return None

        try:
            parts = last_line.split(",")
            value = float(parts[1])
            new_pos = len(content.encode("utf-8"))
            return {"latest_value": value, "new_pos": new_pos}
        except (ValueError, IndexError):
            return None

    async def _read_hist_incremental(
        self,
        ssh_service,
        log_path: str,
        last_pos: int
    ) -> Optional[Dict]:
        """
        增量读取直方图日志

        Returns:
            {
                "histograms": [
                    {延迟桶边界(微秒): 样本数, ...},
                    ...
                ],
                "new_pos": int,
            }
        """
        result = await ssh_service.execute_command(
            f"cat {log_path} 2>/dev/null || true",
            timeout=10
        )

        if not result.get("success") or not result.get("stdout"):
            return None

        content = result["stdout"]
        lines = content.split("\n")

        histograms = []
        current_histogram = {}
        last_timestamp = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            try:
                parts = line.split(",")
                if len(parts) < 3:
                    continue
                timestamp = int(parts[0])
                latency_ns = int(parts[1])
                samples = int(parts[2])

                latency_us = latency_ns / 1000.0

                if last_timestamp is None:
                    last_timestamp = timestamp
                elif timestamp != last_timestamp:
                    if current_histogram:
                        histograms.append(current_histogram)
                    current_histogram = {}
                    last_timestamp = timestamp

                if latency_us not in current_histogram:
                    current_histogram[latency_us] = 0
                current_histogram[latency_us] += samples

            except (ValueError, IndexError):
                continue

        if current_histogram:
            histograms.append(current_histogram)

        if not histograms:
            return None

        new_pos = len(content.encode("utf-8"))
        return {"histograms": histograms, "new_pos": new_pos}

    def _calculate_percentiles_from_histogram(
        self,
        histogram: Dict[float, int]
    ) -> Dict[str, float]:
        """
        从直方图计算百分位延迟

        Args:
            histogram: {延迟桶边界(微秒): 样本数, ...}

        Returns:
            {"p50": float, "p99": float, "p9999": float, "max_lat_us": float}
        """
        if not histogram:
            return {"p50": 0, "p99": 0, "p9999": 0, "max_lat_us": 0}

        sorted_bins = sorted(histogram.items())
        total_samples = sum(count for _, count in sorted_bins)

        if total_samples == 0:
            return {"p50": 0, "p99": 0, "p9999": 0, "max_lat_us": 0}

        cumulative = 0
        result = {}

        for latency_us, count in sorted_bins:
            cumulative += count
            percentile = (cumulative / total_samples) * 100

            if "p50" not in result and percentile >= 50:
                result["p50"] = latency_us
            if "p99" not in result and percentile >= 99:
                result["p99"] = latency_us
            if "p9999" not in result and percentile >= 99.99:
                result["p9999"] = latency_us

        result["max_lat_us"] = max(histogram.keys())
        return result