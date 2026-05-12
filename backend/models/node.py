"""
节点模型
========
关键增强：
- 密码和私钥使用 EncryptedString 类型，SQLAlchemy 层自动加密/解密
- 新增 health_* 字段用于节点健康检查（见 node_health_service.py）
- to_dict 默认不返回凭据，避免 API 误泄漏
"""
from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator

from core.database import Base
from core.crypto import encrypt, decrypt


class EncryptedString(TypeDecorator):
    """
    自动加密/解密的字符串类型。
    写入数据库前加密，读出时解密，对业务代码完全透明。

    使用 LargeBinary 作为底层存储也可，但字符串 + ENC:v1: 前缀方便
    DBA 在运维时肉眼区分"已加密"还是"历史明文"。
    """
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return encrypt(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return decrypt(value)


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    node_name = Column(String(100), nullable=False, index=True)
    host = Column(String(255), nullable=False)
    port = Column(Integer, default=22, nullable=False)
    login_type = Column(Enum("password", "key"), default="password", nullable=False)
    username = Column(String(100), nullable=False)
    # 密码和私钥改为加密存储
    password = Column(EncryptedString, nullable=True)
    private_key = Column(EncryptedString, nullable=True)

    status = Column(Enum("online", "offline", "testing"), default="offline", nullable=False)
    os_type = Column(String(50), nullable=True)
    cpu_info = Column(String(255), nullable=True)
    memory_info = Column(String(255), nullable=True)
    disk_info = Column(Text, nullable=True)

    # 节点健康相关字段
    last_health_check_at = Column(DateTime(timezone=True), nullable=True)
    last_online_at = Column(DateTime(timezone=True), nullable=True)
    health_fail_count = Column(Integer, default=0, nullable=False)
    health_message = Column(String(500), nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_public = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    creator = relationship("User", backref="nodes")
    partitions = relationship("NodePartition", back_populates="node", cascade="all, delete-orphan")
    task_nodes = relationship("TaskNode", back_populates="node")

    def __repr__(self):
        return f"<Node(id={self.id}, name={self.node_name}, host={self.host}, status={self.status})>"

    def to_dict(self, include_credentials: bool = False):
        """
        Args:
            include_credentials: 默认 False，不返回密码/私钥；只在明确需要时才返回。
                                 这样可防止通过列表 API 误批量泄漏凭据。
        """
        data = {
            "id": self.id,
            "node_name": self.node_name,
            "host": self.host,
            "port": self.port,
            "login_type": self.login_type,
            "username": self.username,
            "status": self.status,
            "os_type": self.os_type,
            "cpu_info": self.cpu_info,
            "memory_info": self.memory_info,
            "disk_info": self.disk_info,
            "created_by": self.created_by,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "partitions": [p.to_dict() for p in self.partitions] if self.partitions else [],

            # 健康信息
            "last_health_check_at": (
                self.last_health_check_at.isoformat() if self.last_health_check_at else None
            ),
            "last_online_at": (
                self.last_online_at.isoformat() if self.last_online_at else None
            ),
            "health_fail_count": self.health_fail_count or 0,
            "health_message": self.health_message,
        }
        if include_credentials:
            data["password"] = self.password
            data["private_key"] = self.private_key
        else:
            # 明确标记"有凭据但不返回"，而不是 None 让前端以为没有
            data["has_password"] = bool(self.password)
            data["has_private_key"] = bool(self.private_key)
        return data


class NodePartition(Base):
    __tablename__ = "node_partitions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    partition_name = Column(String(100), nullable=False)
    mount_point = Column(String(255), nullable=False)
    filesystem = Column(String(50), nullable=True)
    total_size = Column(Integer, nullable=True)       # MB
    available_size = Column(Integer, nullable=True)   # MB
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    node = relationship("Node", back_populates="partitions")
    task_nodes = relationship("TaskNode", back_populates="partition")

    def __repr__(self):
        return f"<NodePartition(id={self.id}, node_id={self.node_id}, name={self.partition_name})>"

    def to_dict(self):
        return {
            "id": self.id,
            "node_id": self.node_id,
            "partition_name": self.partition_name,
            "mount_point": self.mount_point,
            "filesystem": self.filesystem,
            "total_size": self.total_size,
            "available_size": self.available_size,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "used_percentage": self.calculate_used_percentage(),
        }

    def calculate_used_percentage(self):
        if self.total_size and self.available_size is not None:
            used = self.total_size - self.available_size
            return round((used / self.total_size) * 100, 2)
        return 0
