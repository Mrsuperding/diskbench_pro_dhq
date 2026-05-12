"""
基线对比服务
============
将测试结果与基线配置进行对比，计算偏差百分比，标记超出阈值的指标。

基线配置格式 (config_json):
{
  "thresholds": {
    "iops": {
      "warning": 10,        # 偏差百分比，超过此值触发 warning
      "critical": 20,       # 偏差百分比，超过此值触发 critical
      "direction": "lower_is_worse"  # 或 "higher_is_worse"
    },
    "latency": {
      "warning": 15,
      "critical": 30,
      "direction": "higher_is_worse"
    },
    "bandwidth": {
      "warning": 10,
      "critical": 20,
      "direction": "lower_is_worse"
    }
  }
}

偏差计算:
- lower_is_worse: 实际值比基线低 N% 视为偏差
- higher_is_worse: 实际值比基线高 N% 视为偏差

偏差百分比 = ((实际值 - 基线值) / 基线值) * 100
"""
import json
from datetime import datetime
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
from core.database import SessionLocal
from models.task import Task, TaskNode, TaskLog
from models.baseline import PerformanceBaseline


class BaselineComparator:
    """
    基线对比器

    将任务节点测试结果与基线配置进行对比，生成偏差报告。
    """

    # 告警级别
    LEVEL_OK = "ok"
    LEVEL_WARNING = "warning"
    LEVEL_CRITICAL = "critical"

    # 支持对比的指标
    METRIC_IOPS = "iops"
    METRIC_LATENCY = "latency"
    METRIC_BANDWIDTH = "bandwidth"

    def __init__(self, socket_manager):
        self.socket_manager = socket_manager

    async def compare_task_node(
        self,
        task_id: int,
        task_node_id: int,
        baseline_id: int
    ) -> Dict[str, Any]:
        """
        对比单个任务节点与基线

        Args:
            task_id: 任务ID
            task_node_id: 任务节点ID
            baseline_id: 基线配置ID

        Returns:
            {
              "baseline_id": int,
              "baseline_name": str,
              "task_node_id": int,
              "overall_status": "ok" | "warning" | "critical",
              "metrics": {
                "iops": {
                  "actual": float,
                  "baseline": float,
                  "deviation_percent": float,
                  "direction": str,
                  "level": str,
                  "exceeded": bool
                },
                ...
              }
            }
        """
        db = SessionLocal()

        try:
            # 获取任务节点
            task_node = db.query(TaskNode).filter(TaskNode.id == task_node_id).first()
            if not task_node:
                raise ValueError(f"TaskNode {task_node_id} not found")

            # 获取基线配置
            baseline = db.query(PerformanceBaseline).filter(PerformanceBaseline.id == baseline_id).first()
            if not baseline:
                raise ValueError(f"Baseline {baseline_id} not found")

            # 解析基线配置
            config = self._parse_config(baseline.config_json)

            # 获取基线指标值 (PerformanceBaseline 直接存储在列中)
            baseline_metrics = {
                "iops": float(baseline.avg_iops) if baseline.avg_iops else 0,
                "latency": float(baseline.avg_latency_ms) if baseline.avg_latency_ms else 0,
                "bandwidth": float(baseline.avg_bw_mbs) if baseline.avg_bw_mbs else 0,
            }

            # 对比每个指标
            metrics_result = {}
            overall_status = self.LEVEL_OK

            for metric_name in [self.METRIC_IOPS, self.METRIC_LATENCY, self.METRIC_BANDWIDTH]:
                if metric_name not in config.get("thresholds", {}):
                    continue

                threshold = config["thresholds"][metric_name]
                actual_value = self._get_actual_value(task_node, metric_name)

                if actual_value is None:
                    continue

                baseline_value = baseline_metrics.get(metric_name)
                if baseline_value is None or baseline_value == 0:
                    continue

                # 计算偏差百分比
                deviation_percent = ((actual_value - baseline_value) / baseline_value) * 100

                # 判断方向
                direction = threshold.get("direction", "lower_is_worse")
                warning_threshold = threshold.get("warning", 10)
                critical_threshold = threshold.get("critical", warning_threshold * 1.5)

                # 判断是否超出阈值
                if direction == "lower_is_worse":
                    exceeded = deviation_percent < -warning_threshold
                    critical_exceeded = deviation_percent < -critical_threshold
                else:
                    exceeded = deviation_percent > warning_threshold
                    critical_exceeded = deviation_percent > critical_threshold

                # 确定级别
                if critical_exceeded:
                    level = self.LEVEL_CRITICAL
                    if overall_status != self.LEVEL_CRITICAL:
                        overall_status = self.LEVEL_CRITICAL
                elif exceeded:
                    level = self.LEVEL_WARNING
                    if overall_status == self.LEVEL_OK:
                        overall_status = self.LEVEL_WARNING
                else:
                    level = self.LEVEL_OK

                metrics_result[metric_name] = {
                    "actual": actual_value,
                    "baseline": baseline_value,
                    "deviation_percent": round(deviation_percent, 2),
                    "direction": direction,
                    "warning_threshold": warning_threshold,
                    "critical_threshold": critical_threshold,
                    "level": level,
                    "exceeded": exceeded
                }

            result = {
                "baseline_id": baseline_id,
                "baseline_name": baseline.name,
                "task_node_id": task_node_id,
                "overall_status": overall_status,
                "metrics": metrics_result
            }

            # 记录日志
            await self._log_comparison_result(db, task_id, result)

            # 通知 WebSocket
            await self.socket_manager.broadcast_to_task(
                str(task_id),
                "baseline_comparison",
                result
            )

            return result

        finally:
            db.close()

    async def compare_task_all_nodes(
        self,
        task_id: int,
        baseline_id: int
    ) -> List[Dict[str, Any]]:
        """
        对比任务的所有节点与基线

        Returns:
            List of comparison results
        """
        db = SessionLocal()

        try:
            task_nodes = db.query(TaskNode).filter(
                TaskNode.task_id == task_id,
                TaskNode.status == "completed"
            ).all()

            results = []
            for tn in task_nodes:
                try:
                    result = await self.compare_task_node(task_id, tn.id, baseline_id)
                    results.append(result)
                except Exception as e:
                    results.append({
                        "task_node_id": tn.id,
                        "error": str(e)
                    })

            return results

        finally:
            db.close()

    def _parse_config(self, config_json: Optional[str]) -> Dict:
        """解析基线配置 JSON"""
        if not config_json:
            return {}
        try:
            return json.loads(config_json)
        except json.JSONDecodeError:
            return {}

    def _get_actual_value(self, task_node: TaskNode, metric_name: str) -> Optional[float]:
        """从任务节点获取实际指标值"""
        if metric_name == self.METRIC_IOPS:
            return float(task_node.iops) if task_node.iops else None
        elif metric_name == self.METRIC_LATENCY:
            return float(task_node.latency) if task_node.latency else None
        elif metric_name == self.METRIC_BANDWIDTH:
            return float(task_node.bandwidth) if task_node.bandwidth else None
        return None

    async def _log_comparison_result(self, db: Session, task_id: int, result: Dict):
        """记录对比结果到日志"""
        level = result.get("overall_status", "ok")
        metrics = result.get("metrics", {})

        # 生成摘要消息
        exceeded_metrics = [
            name for name, m in metrics.items()
            if m.get("exceeded", False)
        ]

        if exceeded_metrics:
            message = (
                f"基线对比完成: {result['baseline_name']}, "
                f"超出阈值指标: {', '.join(exceeded_metrics)}, "
                f"整体状态: {level}"
            )
        else:
            message = (
                f"基线对比完成: {result['baseline_name']}, "
                f"所有指标正常, 整体状态: {level}"
            )

        log_entry = TaskLog(
            task_id=task_id,
            log_level="info" if level == "ok" else "warning",
            message=message,
            source="baseline_comparator"
        )
        db.add(log_entry)
        db.commit()