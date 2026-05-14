from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, Text, DECIMAL, ForeignKey, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(Enum("pending", "running", "completed", "failed", "cancelled"), 
                   default="pending", nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Integer, default=0)  # 秒
    total_io_ops = Column(BigInteger, default=0)
    avg_iops = Column(DECIMAL(10, 2), default=0)
    avg_latency = Column(DECIMAL(10, 2), default=0)
    avg_bw = Column(DECIMAL(10, 2), default=0)  # MB/s
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    creator = relationship("User", backref="tasks")
    test_case = relationship("TestCase", back_populates="tasks")
    task_nodes = relationship("TaskNode", back_populates="task", cascade="all, delete-orphan")
    logs = relationship("TaskLog", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task(id={self.id}, name={self.task_name}, status={self.status})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "task_name": self.task_name,
            "description": self.description,
            "status": self.status,
            "created_by": self.created_by,
            "test_case_id": self.test_case_id,
            "is_public": self.is_public,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "total_io_ops": self.total_io_ops,
            "avg_iops": float(self.avg_iops) if self.avg_iops else 0,
            "avg_latency": float(self.avg_latency) if self.avg_latency else 0,
            "avg_bw": float(self.avg_bw) if self.avg_bw else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "test_case": self.test_case.to_dict() if self.test_case else None,
            "task_nodes": [tn.to_dict() for tn in self.task_nodes] if self.task_nodes else []
        }

class TaskNode(Base):
    __tablename__ = "task_nodes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    partition_id = Column(Integer, ForeignKey("node_partitions.id"), nullable=True)
    # 支持多个分区：逗号分隔的分区路径
    partitions = Column(Text, nullable=True)
    status = Column(Enum("pending", "running", "completed", "failed", "cancelled"),
                   default="pending", nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Integer, default=0)  # 秒
    io_ops = Column(BigInteger, default=0)
    iops = Column(DECIMAL(10, 2), default=0)
    latency = Column(DECIMAL(10, 2), default=0)
    bandwidth = Column(DECIMAL(10, 2), default=0)  # MB/s
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    task = relationship("Task", back_populates="task_nodes")
    node = relationship("Node", back_populates="task_nodes")
    partition = relationship("NodePartition", back_populates="task_nodes")
    performance_data = relationship("IOPerformanceData", back_populates="task_node", cascade="all, delete-orphan")
    iostat_data = relationship("IOStatData", back_populates="task_node", cascade="all, delete-orphan")
    percentiles = relationship("TestResultPercentile", back_populates="task_node", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TaskNode(id={self.id}, task_id={self.task_id}, node_id={self.node_id}, status={self.status})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "node_id": self.node_id,
            "partition_id": self.partition_id,
            "partitions": self.partitions or "",
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
            "node": self.node.to_dict() if self.node else None,
            "partition": self.partition.to_dict() if self.partition else None,
            "percentiles": [p.to_dict() for p in self.percentiles] if self.percentiles else []
        }

class IOPerformanceData(Base):
    __tablename__ = "io_performance_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_node_id = Column(Integer, ForeignKey("task_nodes.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    # 数据来源：fio（FIO测试结果）、monitor（性能监控采样）
    source = Column(String(20), default="fio")
    # 测试类型：read、write（仅 fio 结果有值，monitor 结果为 None）
    test_type = Column(String(20), nullable=True)
    iops = Column(DECIMAL(10, 2), nullable=False)
    bandwidth = Column(DECIMAL(10, 2), nullable=False)  # MB/s
    latency = Column(DECIMAL(10, 2), nullable=False)  # ms
    read_iops = Column(DECIMAL(10, 2), default=0)
    write_iops = Column(DECIMAL(10, 2), default=0)
    read_bw = Column(DECIMAL(10, 2), default=0)  # MB/s
    write_bw = Column(DECIMAL(10, 2), default=0)  # MB/s
    read_lat = Column(DECIMAL(10, 2), default=0)  # ms
    write_lat = Column(DECIMAL(10, 2), default=0)  # ms
    cpu_usage = Column(DECIMAL(5, 2), default=0)  # %
    memory_usage = Column(DECIMAL(5, 2), default=0)  # %
    # 百分位延迟（微秒），仅 fio 结果有值
    p50_lat_us = Column(DECIMAL(15, 2), default=0)
    p75_lat_us = Column(DECIMAL(15, 2), default=0)
    p90_lat_us = Column(DECIMAL(15, 2), default=0)
    p95_lat_us = Column(DECIMAL(15, 2), default=0)
    p99_lat_us = Column(DECIMAL(15, 2), default=0)
    p999_lat_us = Column(DECIMAL(15, 2), default=0)
    p9999_lat_us = Column(DECIMAL(15, 2), default=0)
    max_lat_us = Column(DECIMAL(15, 2), default=0)  # 最大延迟（微秒）

    # 关系
    task_node = relationship("TaskNode", back_populates="performance_data")

    def __repr__(self):
        return f"<IOPerformanceData(id={self.id}, task_node_id={self.task_node_id}, source={self.source})>"

    def to_dict(self):
        return {
            "id": self.id,
            "task_node_id": self.task_node_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "source": self.source,
            "test_type": self.test_type,
            "iops": float(self.iops) if self.iops else 0,
            "bandwidth": float(self.bandwidth) if self.bandwidth else 0,
            "latency": float(self.latency) if self.latency else 0,
            "read_iops": float(self.read_iops) if self.read_iops else 0,
            "write_iops": float(self.write_iops) if self.write_iops else 0,
            "read_bw": float(self.read_bw) if self.read_bw else 0,
            "write_bw": float(self.write_bw) if self.write_bw else 0,
            "read_lat": float(self.read_lat) if self.read_lat else 0,
            "write_lat": float(self.write_lat) if self.write_lat else 0,
            "cpu_usage": float(self.cpu_usage) if self.cpu_usage else 0,
            "memory_usage": float(self.memory_usage) if self.memory_usage else 0,
            "p50_lat_us": float(self.p50_lat_us) if self.p50_lat_us else 0,
            "p75_lat_us": float(self.p75_lat_us) if self.p75_lat_us else 0,
            "p90_lat_us": float(self.p90_lat_us) if self.p90_lat_us else 0,
            "p95_lat_us": float(self.p95_lat_us) if self.p95_lat_us else 0,
            "p99_lat_us": float(self.p99_lat_us) if self.p99_lat_us else 0,
            "p999_lat_us": float(self.p999_lat_us) if self.p999_lat_us else 0,
            "p9999_lat_us": float(self.p9999_lat_us) if self.p9999_lat_us else 0,
            "max_lat_us": float(self.max_lat_us) if self.max_lat_us else 0,
        }

class IOStatData(Base):
    __tablename__ = "iostat_data"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_node_id = Column(Integer, ForeignKey("task_nodes.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    device = Column(String(50), nullable=False)
    tps = Column(DECIMAL(10, 2), nullable=False)  # 每秒传输次数
    kB_read_s = Column(DECIMAL(10, 2), nullable=False)  # kB/s
    kB_wrtn_s = Column(DECIMAL(10, 2), nullable=False)  # kB/s
    kB_dscd_s = Column(DECIMAL(10, 2), default=0)  # kB/s
    kB_read = Column(BigInteger, default=0)  # 总读取量
    kB_wrtn = Column(BigInteger, default=0)  # 总写入量
    kB_dscd = Column(BigInteger, default=0)  # 总丢弃量
    rqmps = Column(DECIMAL(10, 2), default=0)  # 每秒合并请求数
    await_time = Column(DECIMAL(10, 2), default=0)  # 平均等待时间
    aqu_sz = Column(DECIMAL(10, 2), default=0)  # 平均队列长度
    util = Column(DECIMAL(5, 2), default=0)  # 利用率 %
    
    # 关系
    task_node = relationship("TaskNode", back_populates="iostat_data")
    
    def __repr__(self):
        return f"<IOStatData(id={self.id}, task_node_id={self.task_node_id}, device={self.device})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "task_node_id": self.task_node_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "device": self.device,
            "tps": float(self.tps) if self.tps else 0,
            "kB_read_s": float(self.kB_read_s) if self.kB_read_s else 0,
            "kB_wrtn_s": float(self.kB_wrtn_s) if self.kB_wrtn_s else 0,
            "kB_dscd_s": float(self.kB_dscd_s) if self.kB_dscd_s else 0,
            "kB_read": self.kB_read,
            "kB_wrtn": self.kB_wrtn,
            "kB_dscd": self.kB_dscd,
            "rqmps": float(self.rqmps) if self.rqmps else 0,
            "await_time": float(self.await_time) if self.await_time else 0,
            "aqu_sz": float(self.aqu_sz) if self.aqu_sz else 0,
            "util": float(self.util) if self.util else 0
        }


class TaskLog(Base):
    __tablename__ = "task_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    log_level = Column(Enum("debug", "info", "warning", "error"), default="info", nullable=False)
    message = Column(Text, nullable=False)
    source = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    task = relationship("Task", back_populates="logs")
    
    def __repr__(self):
        return f"<TaskLog(id={self.id}, task_id={self.task_id}, level={self.log_level})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "log_level": self.log_level,
            "message": self.message,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }