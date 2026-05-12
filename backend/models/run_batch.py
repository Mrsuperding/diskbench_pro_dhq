"""
多运行批次（Run Batch）
=======================
压测常见需求：同一个测试用例要跑 N 次（比如 5 次），然后自动计算各次结果的
平均值 / 中位数 / 标准差 / P95，来判断结果是否稳定。

RunBatch 是"一组任务"的容器：
- batch_size: 计划运行次数
- 每次实际运行会产生一个 Task，记录在 RunBatchItem
- 全部完成后触发聚合计算，把统计值写到 RunBatch 上

这比"一次任务内 numjobs=N"更灵活：多次运行可以捕捉到跨时间维度的波动，
更能代表真实生产环境的性能稳定性。
"""
from __future__ import annotations

import statistics
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Column, Integer, String, DateTime, Text, ForeignKey, DECIMAL, Enum, Boolean
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Session

from core.database import Base, SessionLocal
from models.task import Task, TaskNode


class RunBatch(Base):
    __tablename__ = "run_batches"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # 模板任务：每个子运行都用这个任务的配置克隆一个新 Task
    template_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)

    batch_size = Column(Integer, nullable=False)      # 计划次数
    interval_seconds = Column(Integer, default=30, nullable=False)  # 两次之间的间隔（秒）

    status = Column(
        Enum("pending", "running", "completed", "failed", "cancelled"),
        default="pending",
        nullable=False,
    )

    # 聚合结果（全部子任务跑完后计算）
    avg_iops = Column(DECIMAL(12, 2), default=0)
    median_iops = Column(DECIMAL(12, 2), default=0)
    stdev_iops = Column(DECIMAL(12, 2), default=0)
    cv_iops = Column(DECIMAL(6, 2), default=0)        # 变异系数 = stdev / avg，反映稳定性
    p95_iops = Column(DECIMAL(12, 2), default=0)

    avg_latency_ms = Column(DECIMAL(12, 2), default=0)
    median_latency_ms = Column(DECIMAL(12, 2), default=0)
    stdev_latency_ms = Column(DECIMAL(12, 2), default=0)

    avg_bw_mbs = Column(DECIMAL(12, 2), default=0)
    median_bw_mbs = Column(DECIMAL(12, 2), default=0)
    stdev_bw_mbs = Column(DECIMAL(12, 2), default=0)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    items = relationship("RunBatchItem", back_populates="batch", cascade="all, delete-orphan",
                         order_by="RunBatchItem.run_index")

    def to_dict(self, include_items: bool = True):
        d = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "template_task_id": self.template_task_id,
            "batch_size": self.batch_size,
            "interval_seconds": self.interval_seconds,
            "status": self.status,
            "avg_iops": float(self.avg_iops or 0),
            "median_iops": float(self.median_iops or 0),
            "stdev_iops": float(self.stdev_iops or 0),
            "cv_iops": float(self.cv_iops or 0),
            "p95_iops": float(self.p95_iops or 0),
            "avg_latency_ms": float(self.avg_latency_ms or 0),
            "median_latency_ms": float(self.median_latency_ms or 0),
            "stdev_latency_ms": float(self.stdev_latency_ms or 0),
            "avg_bw_mbs": float(self.avg_bw_mbs or 0),
            "median_bw_mbs": float(self.median_bw_mbs or 0),
            "stdev_bw_mbs": float(self.stdev_bw_mbs or 0),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_items:
            d["items"] = [i.to_dict() for i in (self.items or [])]
        return d


class RunBatchItem(Base):
    __tablename__ = "run_batch_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    batch_id = Column(Integer, ForeignKey("run_batches.id"), nullable=False, index=True)
    run_index = Column(Integer, nullable=False)     # 1..batch_size
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)  # 实际跑出的任务
    status = Column(String(20), default="pending", nullable=False)
    avg_iops = Column(DECIMAL(12, 2), default=0)
    avg_latency_ms = Column(DECIMAL(12, 2), default=0)
    avg_bw_mbs = Column(DECIMAL(12, 2), default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    batch = relationship("RunBatch", back_populates="items")

    def to_dict(self):
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "run_index": self.run_index,
            "task_id": self.task_id,
            "status": self.status,
            "avg_iops": float(self.avg_iops or 0),
            "avg_latency_ms": float(self.avg_latency_ms or 0),
            "avg_bw_mbs": float(self.avg_bw_mbs or 0),
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class RunBatchService:
    """多运行批次的执行和聚合计算"""

    @staticmethod
    def create_batch(
        db: Session,
        *,
        name: str,
        template_task_id: int,
        batch_size: int,
        interval_seconds: int = 30,
        description: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> Optional[RunBatch]:
        batch_size = max(1, min(batch_size, 100))  # 1..100
        batch = RunBatch(
            name=name,
            description=description,
            template_task_id=template_task_id,
            batch_size=batch_size,
            interval_seconds=interval_seconds,
            created_by=created_by,
            status="pending",
        )
        db.add(batch)
        db.flush()
        # 创建占位 item
        for i in range(1, batch_size + 1):
            db.add(RunBatchItem(batch_id=batch.id, run_index=i, status="pending"))
        db.commit()
        db.refresh(batch)
        return batch

    @staticmethod
    async def run_batch(batch_id: int, task_service):
        """
        执行一个批次。task_service 是 TaskService 实例，用来调用 execute_task。
        该方法由 API 路由发起 BackgroundTask 调度，内部自建 session。
        """
        import asyncio

        db = SessionLocal()
        try:
            batch = db.query(RunBatch).filter(RunBatch.id == batch_id).first()
            if not batch or batch.status != "pending":
                return
            batch.status = "running"
            batch.started_at = datetime.utcnow()
            db.commit()

            # 取模板
            template = db.query(Task).filter(Task.id == batch.template_task_id).first()
            template_nodes = (
                db.query(TaskNode).filter(TaskNode.task_id == batch.template_task_id).all()
                if template else []
            )
            if not template or not template_nodes:
                batch.status = "failed"
                db.commit()
                return

            items = sorted(batch.items or [], key=lambda i: i.run_index)
            for item in items:
                # 克隆一次任务
                new_task = Task(
                    task_name=f"{batch.name} · run #{item.run_index}",
                    description=f"由批次 #{batch.id} 运行",
                    status="pending",
                    created_by=batch.created_by or template.created_by,
                    test_case_id=template.test_case_id,
                    is_public=template.is_public,
                    start_time=datetime.utcnow(),
                )
                db.add(new_task)
                db.flush()
                for tn in template_nodes:
                    db.add(TaskNode(
                        task_id=new_task.id,
                        node_id=tn.node_id,
                        partition_id=tn.partition_id,
                        status="pending",
                        start_time=datetime.utcnow(),
                    ))
                item.task_id = new_task.id
                item.status = "running"
                item.started_at = datetime.utcnow()
                db.commit()

                # 串行执行（多次压测必须串行，避免互相干扰）
                try:
                    await task_service.execute_task(new_task.id)
                except Exception as e:
                    item.error_message = str(e)[:500]

                # 回读 task 的结果
                t = db.query(Task).filter(Task.id == new_task.id).first()
                item.status = t.status if t else "failed"
                item.completed_at = datetime.utcnow()
                if t:
                    item.avg_iops = float(t.avg_iops or 0)
                    item.avg_latency_ms = float(t.avg_latency or 0)
                    item.avg_bw_mbs = float(t.avg_bw or 0)
                db.commit()

                # 两次之间休息一段时间，让系统状态恢复
                if item.run_index < batch.batch_size:
                    await asyncio.sleep(batch.interval_seconds)

            # 聚合计算
            RunBatchService._aggregate(db, batch)
        except Exception as e:
            print(f"[run_batch] error: {e}")
            batch = db.query(RunBatch).filter(RunBatch.id == batch_id).first()
            if batch:
                batch.status = "failed"
                batch.completed_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()

    # ------------------------------------------------------------ 聚合 ----

    @staticmethod
    def _aggregate(db: Session, batch: RunBatch):
        completed_items = [i for i in batch.items if i.status == "completed"]
        if not completed_items:
            batch.status = "failed"
            batch.completed_at = datetime.utcnow()
            db.commit()
            return

        iops = [float(i.avg_iops or 0) for i in completed_items]
        lat = [float(i.avg_latency_ms or 0) for i in completed_items]
        bw = [float(i.avg_bw_mbs or 0) for i in completed_items]

        def _p95(values):
            if not values:
                return 0.0
            s = sorted(values)
            idx = min(len(s) - 1, max(0, int(0.95 * len(s)) - 1))
            return s[idx]

        batch.avg_iops = statistics.mean(iops) if iops else 0
        batch.median_iops = statistics.median(iops) if iops else 0
        batch.stdev_iops = statistics.pstdev(iops) if len(iops) > 1 else 0
        batch.cv_iops = (
            float(batch.stdev_iops) / float(batch.avg_iops) * 100
            if batch.avg_iops else 0
        )
        batch.p95_iops = _p95(iops)

        batch.avg_latency_ms = statistics.mean(lat) if lat else 0
        batch.median_latency_ms = statistics.median(lat) if lat else 0
        batch.stdev_latency_ms = statistics.pstdev(lat) if len(lat) > 1 else 0

        batch.avg_bw_mbs = statistics.mean(bw) if bw else 0
        batch.median_bw_mbs = statistics.median(bw) if bw else 0
        batch.stdev_bw_mbs = statistics.pstdev(bw) if len(bw) > 1 else 0

        batch.status = "completed"
        batch.completed_at = datetime.utcnow()
        db.commit()
