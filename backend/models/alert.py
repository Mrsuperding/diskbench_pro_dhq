"""
告警模型
========

AlertRule：告警规则（谁来监控、监控什么指标、触发条件、通知方式）
AlertEvent：一次告警触发的实例

支持的指标：
- iops / bandwidth / latency / cpu_usage

支持的比较：
- gt / lt / ge / le

支持的通知渠道（通道字段可填：）
- webhook / email / log

告警去重：
- 连续触发会用 dedup_window_minutes 合并（默认 5 分钟），避免告警风暴
"""
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, ForeignKey,
    DECIMAL, Enum, Index,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.database import Base


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # 监控范围：
    # - 为 null 时表示"所有任务"
    # - 指定 task_id 只监控该任务
    # - 指定 test_case_id 只监控该用例派生出的所有任务
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=True)

    # 指标 + 触发条件
    metric = Column(
        Enum("iops", "bandwidth", "latency", "cpu_usage", "memory_usage"),
        nullable=False,
    )
    operator = Column(
        Enum("gt", "lt", "ge", "le"), default="gt", nullable=False
    )
    threshold = Column(DECIMAL(15, 4), nullable=False)

    # 需要持续多少个采样点满足条件才触发（过滤瞬时毛刺）
    consecutive_points = Column(Integer, default=3, nullable=False)

    # 告警合并窗口（分钟）：同规则同对象 N 分钟内重复触发只算一次
    dedup_window_minutes = Column(Integer, default=5, nullable=False)

    # 通知通道（多个用英文逗号分隔）：log,webhook,email
    channels = Column(String(200), default="log", nullable=False)
    webhook_url = Column(String(500), nullable=True)
    email_to = Column(String(500), nullable=True)

    # 严重程度：info / warning / critical
    severity = Column(
        Enum("info", "warning", "critical"),
        default="warning",
        nullable=False,
    )

    enabled = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    events = relationship("AlertEvent", back_populates="rule", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "task_id": self.task_id,
            "test_case_id": self.test_case_id,
            "metric": self.metric,
            "operator": self.operator,
            "threshold": float(self.threshold or 0),
            "consecutive_points": self.consecutive_points or 3,
            "dedup_window_minutes": self.dedup_window_minutes or 5,
            "channels": (self.channels or "log").split(","),
            "webhook_url": self.webhook_url,
            "email_to": self.email_to,
            "severity": self.severity,
            "enabled": self.enabled,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=False, index=True)

    # 触发源
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True, index=True)
    task_node_id = Column(Integer, ForeignKey("task_nodes.id"), nullable=True)

    metric = Column(String(50), nullable=False)
    observed_value = Column(DECIMAL(15, 4), nullable=False)
    threshold = Column(DECIMAL(15, 4), nullable=False)
    severity = Column(String(20), nullable=False, default="warning")

    message = Column(Text, nullable=True)
    notification_sent = Column(Boolean, default=False, nullable=False)
    notification_error = Column(Text, nullable=True)

    triggered_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    rule = relationship("AlertRule", back_populates="events")

    __table_args__ = (
        Index("ix_alert_event_rule_time", "rule_id", "triggered_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "task_id": self.task_id,
            "task_node_id": self.task_node_id,
            "metric": self.metric,
            "observed_value": float(self.observed_value or 0),
            "threshold": float(self.threshold or 0),
            "severity": self.severity,
            "message": self.message,
            "notification_sent": self.notification_sent,
            "notification_error": self.notification_error,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
