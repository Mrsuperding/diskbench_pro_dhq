"""
任务调度模型
============
支持三种触发方式：
- once:  在指定时间执行一次
- interval: 每 N 分钟执行一次（从 start_at 开始）
- cron:  使用标准 cron 表达式（分 时 日 月 周）

schedule 与 task 的关系：
    ScheduledTask 是"调度配置"，触发时会基于 template_task_id 指向的任务
    克隆一个新的 Task 实例并执行，这样历史任务记录按次独立保留，方便做趋势分析。
"""
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Boolean, Enum, DateTime, Text, ForeignKey
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.database import Base


class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # 模板任务：调度器每次触发时克隆这个任务的配置跑一次
    template_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)

    # 触发方式
    trigger_type = Column(
        Enum("once", "interval", "cron"),
        default="interval",
        nullable=False,
    )

    # once：执行时间
    run_at = Column(DateTime(timezone=True), nullable=True)

    # interval：每 N 分钟执行一次（从 start_at 开始）
    interval_minutes = Column(Integer, nullable=True)
    start_at = Column(DateTime(timezone=True), nullable=True)
    end_at = Column(DateTime(timezone=True), nullable=True)   # 可选：结束时间

    # cron：标准 5 字段 cron 表达式（分 时 日 月 周）
    cron_expr = Column(String(100), nullable=True)

    # 运行状态
    enabled = Column(Boolean, default=True, nullable=False)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    last_run_task_id = Column(Integer, nullable=True)     # 最近一次实际运行的任务 id
    last_run_status = Column(String(20), nullable=True)   # success / failed / skipped
    last_run_message = Column(Text, nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    run_count = Column(Integer, default=0, nullable=False)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return (
            f"<ScheduledTask(id={self.id}, name={self.name}, "
            f"trigger={self.trigger_type}, enabled={self.enabled})>"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "template_task_id": self.template_task_id,
            "trigger_type": self.trigger_type,
            "run_at": self.run_at.isoformat() if self.run_at else None,
            "interval_minutes": self.interval_minutes,
            "start_at": self.start_at.isoformat() if self.start_at else None,
            "end_at": self.end_at.isoformat() if self.end_at else None,
            "cron_expr": self.cron_expr,
            "enabled": self.enabled,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "last_run_task_id": self.last_run_task_id,
            "last_run_status": self.last_run_status,
            "last_run_message": self.last_run_message,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "run_count": self.run_count or 0,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
