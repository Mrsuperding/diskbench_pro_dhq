"""
审计日志模型
============
记录谁（用户）、在什么时间、对什么资源、做了什么操作，以及来源 IP 和 User-Agent。

目的：
- 合规要求：压测平台会操作生产节点 SSH，审计必不可少
- 排障：某个任务被意外删除/修改时能追溯到人
- 安全：识别异常登录和越权操作
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.sql import func
from core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # 谁
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    username = Column(String(100), nullable=True)  # 冗余存一份，用户被删后仍能看到操作历史

    # 做了什么
    action = Column(String(100), nullable=False, index=True)
    # 对什么资源（node/task/case/baseline/schedule/user...）
    resource_type = Column(String(50), nullable=True, index=True)
    resource_id = Column(String(50), nullable=True)   # 用 String 以兼容 UUID/整数

    # 结果
    status = Column(String(20), default="success", nullable=False)  # success / failure
    message = Column(Text, nullable=True)

    # 来源信息
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_method = Column(String(10), nullable=True)   # GET/POST/...
    request_path = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # 组合索引：按资源类型+时间倒序查询是最常见的场景
    __table_args__ = (
        Index("ix_audit_resource_time", "resource_type", "resource_id", "created_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "status": self.status,
            "message": self.message,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "request_method": self.request_method,
            "request_path": self.request_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
