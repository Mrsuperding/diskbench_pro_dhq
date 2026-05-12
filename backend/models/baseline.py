"""
基准模型
========
Baseline 记录某次任务执行结果作为"性能基准"，后续任务可以与它做对比。

典型场景：
- 生产环境某次压测表现良好，标记为基准
- 下次代码变更/硬件升级后重新跑同样的任务
- 平台自动对比两次结果，告知 IOPS/延迟/带宽的变化幅度

一次测试用例 test_case 可以有多个基准（比如"硬件基准"、"生产稳定版基准"），
但同一时刻只有一个 is_active。

支持两种阈值配置模式：
1. 简单模式（兼容旧版）：使用 iops_tolerance_pct 等百分比字段
2. 高级模式（新版）：使用 config_json 配置阈值规则和偏差方向
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, DECIMAL
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.database import Base


class PerformanceBaseline(Base):
    __tablename__ = "performance_baselines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # 来源任务
    source_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)

    # 测试用例（用来找"同类任务"做对比）
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=False)

    # 快照：从 source_task 复制出基准数值，防止 source_task 被删除影响基准
    avg_iops = Column(DECIMAL(12, 2), nullable=False, default=0)
    avg_latency_ms = Column(DECIMAL(12, 2), nullable=False, default=0)
    avg_bw_mbs = Column(DECIMAL(12, 2), nullable=False, default=0)
    p95_iops = Column(DECIMAL(12, 2), nullable=True)
    p95_latency_ms = Column(DECIMAL(12, 2), nullable=True)

    # 简单阈值（百分比）：超出这个阈值视为性能变化显著
    iops_tolerance_pct = Column(DECIMAL(5, 2), default=10.0, nullable=False)
    latency_tolerance_pct = Column(DECIMAL(5, 2), default=10.0, nullable=False)
    bw_tolerance_pct = Column(DECIMAL(5, 2), default=10.0, nullable=False)

    # 高级阈值配置（JSON格式），优先级高于简单阈值
    # 格式: {
    #   "thresholds": {
    #     "iops": {"warning": 10, "critical": 20, "direction": "lower_is_worse"},
    #     "latency": {"warning": 15, "critical": 30, "direction": "higher_is_worse"},
    #     "bandwidth": {"warning": 10, "critical": 20, "direction": "lower_is_worse"}
    #   }
    # }
    config_json = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False, index=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Baseline(id={self.id}, name={self.name}, active={self.is_active})>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "source_task_id": self.source_task_id,
            "test_case_id": self.test_case_id,
            "avg_iops": float(self.avg_iops or 0),
            "avg_latency_ms": float(self.avg_latency_ms or 0),
            "avg_bw_mbs": float(self.avg_bw_mbs or 0),
            "p95_iops": float(self.p95_iops) if self.p95_iops is not None else None,
            "p95_latency_ms": float(self.p95_latency_ms) if self.p95_latency_ms is not None else None,
            "iops_tolerance_pct": float(self.iops_tolerance_pct or 10.0),
            "latency_tolerance_pct": float(self.latency_tolerance_pct or 10.0),
            "bw_tolerance_pct": float(self.bw_tolerance_pct or 10.0),
            "config_json": self.config_json,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
