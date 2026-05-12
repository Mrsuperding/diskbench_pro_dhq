"""
数据保留策略
============
长期运行的压测平台数据会快速膨胀，默认 IOPerformanceData / IOStatData 每节点每秒几条，
一周就能写满几千万行。需要自动清理过期数据。

保留策略（可通过环境变量覆盖，在 core/config.py 里读）：
  RETENTION_METRICS_DAYS     性能/iostat 采样数据保留天数，默认 30
  RETENTION_TASK_LOGS_DAYS   任务日志保留天数，默认 60
  RETENTION_AUDIT_DAYS       审计日志保留天数，默认 90
  RETENTION_ALERTS_DAYS      告警事件保留天数，默认 90

注意：
- 已归档为基准的任务（被 baselines 引用）不会清理其详细采样数据
- 任务本身（Task / TaskNode 行）默认不清理，只清理大表（采样数据），
  因为任务表很小且有分析价值
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

from sqlalchemy.orm import Session

from core.database import SessionLocal
from models.task import IOPerformanceData, IOStatData, TaskLog, TaskNode
from models.baseline import PerformanceBaseline


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


class RetentionService:
    """数据保留与定期清理"""

    # 每天凌晨 3 点左右跑一次
    _RUN_INTERVAL_HOURS = 24

    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._stopped = asyncio.Event()

    # -------------------------------------------------------------- 后台循环 ----

    def start(self):
        self._stopped.clear()
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        self._stopped.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _loop(self):
        # 启动后先等 60s 再开始第一轮，避免启动期压力
        await asyncio.sleep(60)
        while not self._stopped.is_set():
            try:
                stats = await asyncio.get_event_loop().run_in_executor(None, self.run_once)
                print(f"[retention] cleanup done: {stats}")
            except Exception as e:
                print(f"[retention] cycle error: {e}")
            try:
                await asyncio.wait_for(
                    self._stopped.wait(),
                    timeout=self._RUN_INTERVAL_HOURS * 3600,
                )
            except asyncio.TimeoutError:
                pass

    # -------------------------------------------------------------- 实际清理 ----

    def run_once(self) -> Dict[str, int]:
        """执行一次清理，返回各表删除行数统计"""
        stats: Dict[str, int] = {}

        stats["perf_metrics"] = self._cleanup_performance_metrics(
            days=_env_int("RETENTION_METRICS_DAYS", 30)
        )
        stats["iostat"] = self._cleanup_iostat(
            days=_env_int("RETENTION_METRICS_DAYS", 30)
        )
        stats["task_logs"] = self._cleanup_task_logs(
            days=_env_int("RETENTION_TASK_LOGS_DAYS", 60)
        )
        stats["audit_logs"] = self._cleanup_audit_logs(
            days=_env_int("RETENTION_AUDIT_DAYS", 90)
        )
        stats["alert_events"] = self._cleanup_alert_events(
            days=_env_int("RETENTION_ALERTS_DAYS", 90)
        )
        return stats

    def _cleanup_performance_metrics(self, days: int) -> int:
        """
        清理过期的性能采样。
        保留条件：task_node 关联的任务是某个基准的 source_task → 不清理
        """
        if days <= 0:
            return 0
        db = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)

            # 找出所有被基准引用的 task_id
            protected_task_ids = {
                row[0] for row in
                db.query(PerformanceBaseline.source_task_id).distinct().all()
            }

            # 找出受保护的 task_node_id
            protected_node_ids = set()
            if protected_task_ids:
                rows = (
                    db.query(TaskNode.id)
                    .filter(TaskNode.task_id.in_(protected_task_ids))
                    .all()
                )
                protected_node_ids = {r[0] for r in rows}

            q = db.query(IOPerformanceData).filter(IOPerformanceData.timestamp < cutoff)
            if protected_node_ids:
                q = q.filter(~IOPerformanceData.task_node_id.in_(protected_node_ids))

            deleted = q.delete(synchronize_session=False)
            db.commit()
            return deleted
        except Exception as e:
            db.rollback()
            print(f"[retention] perf cleanup error: {e}")
            return 0
        finally:
            db.close()

    def _cleanup_iostat(self, days: int) -> int:
        if days <= 0:
            return 0
        db = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            # iostat 保留策略与 performance 一致
            protected_task_ids = {
                row[0] for row in
                db.query(PerformanceBaseline.source_task_id).distinct().all()
            }
            protected_node_ids = set()
            if protected_task_ids:
                rows = (
                    db.query(TaskNode.id)
                    .filter(TaskNode.task_id.in_(protected_task_ids))
                    .all()
                )
                protected_node_ids = {r[0] for r in rows}
            q = db.query(IOStatData).filter(IOStatData.timestamp < cutoff)
            if protected_node_ids:
                q = q.filter(~IOStatData.task_node_id.in_(protected_node_ids))
            deleted = q.delete(synchronize_session=False)
            db.commit()
            return deleted
        except Exception as e:
            db.rollback()
            print(f"[retention] iostat cleanup error: {e}")
            return 0
        finally:
            db.close()

    def _cleanup_task_logs(self, days: int) -> int:
        if days <= 0:
            return 0
        db = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            deleted = (
                db.query(TaskLog)
                .filter(TaskLog.created_at < cutoff)
                .delete(synchronize_session=False)
            )
            db.commit()
            return deleted
        except Exception as e:
            db.rollback()
            print(f"[retention] task_logs cleanup error: {e}")
            return 0
        finally:
            db.close()

    def _cleanup_audit_logs(self, days: int) -> int:
        """调用 AuditService 的清理方法"""
        try:
            from services.audit_service import AuditService
            return AuditService.cleanup_older_than(days=days)
        except Exception as e:
            print(f"[retention] audit cleanup error: {e}")
            return 0

    def _cleanup_alert_events(self, days: int) -> int:
        if days <= 0:
            return 0
        db = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            from models.alert import AlertEvent
            deleted = (
                db.query(AlertEvent)
                .filter(AlertEvent.triggered_at < cutoff)
                .delete(synchronize_session=False)
            )
            db.commit()
            return deleted
        except Exception as e:
            db.rollback()
            print(f"[retention] alert cleanup error: {e}")
            return 0
        finally:
            db.close()


# 全局单例
retention_service = RetentionService()
