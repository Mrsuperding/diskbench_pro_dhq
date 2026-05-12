"""
任务节点分区关联模型
====================
存储任务-节点-分区的三元关联关系，支持每个节点-分区对配置独立的测试容量限制。
"""
from sqlalchemy import Column, Integer, String, Enum, DateTime, Text, DECIMAL, ForeignKey, Boolean, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base


class TaskNodePartition(Base):
    """
    任务节点分区关联表

    存储任务与节点-分区对之间的关联关系，支持：
    - 多节点并发测试
    - 每节点多分区测试（单任务内每个节点可有多个分区）
    - 每个节点-分区对独立配置测试容量限制（capacity_limit）
    - 初始化写入状态跟踪
    """
    __tablename__ = "task_node_partitions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False, index=True)
    partition_id = Column(Integer, ForeignKey("node_partitions.id"), nullable=False, index=True)

    # 测试容量限制（MB），0 表示无限制
    capacity_limit = Column(Integer, default=0, nullable=False)

    # 初始化写入状态
    init_status = Column(
        Enum("pending", "running", "completed", "failed", "skipped"),
        default="pending",
        nullable=False
    )
    init_start_time = Column(DateTime(timezone=True), nullable=True)
    init_end_time = Column(DateTime(timezone=True), nullable=True)
    init_error = Column(Text, nullable=True)

    # 测试执行状态
    status = Column(
        Enum("pending", "running", "completed", "failed", "cancelled"),
        default="pending",
        nullable=False
    )
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Integer, default=0)

    # 测试结果
    io_ops = Column(BigInteger, default=0)
    iops = Column(DECIMAL(10, 2), default=0)
    latency = Column(DECIMAL(10, 2), default=0)  # ms
    bandwidth = Column(DECIMAL(10, 2), default=0)  # MB/s

    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    task = relationship("Task", backref="task_node_partitions")
    node = relationship("Node")
    partition = relationship("NodePartition")

    def __repr__(self):
        return f"<TaskNodePartition(id={self.id}, task_id={self.task_id}, node_id={self.node_id}, partition_id={self.partition_id})>"

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "node_id": self.node_id,
            "partition_id": self.partition_id,
            "capacity_limit": self.capacity_limit,
            "init_status": self.init_status,
            "init_start_time": self.init_start_time.isoformat() if self.init_start_time else None,
            "init_end_time": self.init_end_time.isoformat() if self.init_end_time else None,
            "init_error": self.init_error,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "io_ops": self.io_ops,
            "iops": float(self.iops) if self.iops else 0,
            "latency": float(self.latency) if self.latency else 0,
            "bandwidth": float(self.bandwidth) if self.bandwidth else 0,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "node": self.node.to_dict() if self.node else None,
            "partition": self.partition.to_dict() if self.partition else None
        }


class TestResultPercentile(Base):
    """
    测试结果百分位数表

    存储 fio histogram 解析后的 P99/P9999 等百分位数数据。
    """
    __tablename__ = "test_result_percentiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_node_id = Column(Integer, ForeignKey("task_nodes.id"), nullable=False, index=True)

    # 百分位名称: p50, p90, p95, p99, p999, p9999
    percentile_name = Column(String(20), nullable=False)

    # 延迟值（微秒）
    latency_us = Column(DECIMAL(15, 2), nullable=False)

    # 关联的测试类型
    test_type = Column(String(50), nullable=True)  # read, write, trim

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    task_node = relationship("TaskNode")

    def __repr__(self):
        return f"<TestResultPercentile(id={self.id}, task_node_id={self.task_node_id}, percentile_name={self.percentile_name}, latency_us={self.latency_us})>"

    def to_dict(self):
        return {
            "id": self.id,
            "task_node_id": self.task_node_id,
            "percentile_name": self.percentile_name,
            "latency_us": float(self.latency_us) if self.latency_us else 0,
            "test_type": self.test_type,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }