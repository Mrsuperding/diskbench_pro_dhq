#!/usr/bin/env python3
"""
数据库初始化脚本
使用 SQLAlchemy 模型自动创建所有表

使用方法:
    python init_database.py                  # 创建所有表
    python init_database.py --drop            # 删除并重建所有表
    python init_database.py --with-data       # 创建表并插入初始数据
"""
import argparse
import sys
from pathlib import Path

# 添加 backend 目录到 Python 路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from core.database import engine, Base, SessionLocal
from models.user import User
from models.node import Node, NodePartition
from models.case import TestCase
from models.task import (
    Task, TaskNode, IOPerformanceData, IOStatData,
    TaskLog
)
from models.task_node_partition import TaskNodePartition, TestResultPercentile
from models.baseline import PerformanceBaseline
from models.audit import AuditLog
from models.alert import AlertRule, AlertEvent
from models.monitor import Monitor
from models.schedule import ScheduledTask
from models.run_batch import RunBatch, RunBatchItem

# 所有模型按依赖顺序排列
MODELS = [
    User,
    Node,
    NodePartition,
    TestCase,
    Task,
    TaskNode,
    IOPerformanceData,
    IOStatData,
    TaskLog,
    TaskNodePartition,
    TestResultPercentile,
    PerformanceBaseline,
    AuditLog,
    AlertRule,
    AlertEvent,
    Monitor,
    ScheduledTask,
    RunBatch,
    RunBatchItem,
]


def create_tables(drop_existing: bool = False):
    """创建所有表"""
    with engine.connect() as conn:
        for model in MODELS:
            table_name = model.__tablename__
            if drop_existing:
                print(f"删除表: {table_name}")
                conn.execute(text(f"DROP TABLE IF EXISTS `{table_name}`"))
            else:
                print(f"创建表: {table_name}")

        # 一次性创建所有表
        Base.metadata.create_all(bind=engine)
        conn.commit()

    print(f"\n✓ 成功创建 {len(MODELS)} 个表")


def insert_initial_data():
    """插入初始数据"""
    db = SessionLocal()
    try:
        # 检查是否已有管理员用户
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("管理员用户已存在，跳过初始化数据")
            return

        # 创建管理员用户 (密码: admin123)
        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyDAXCZ3aKjLXS",
            role="admin",
            is_active=True
        )
        db.add(admin_user)

        # 创建普通用户 (密码: user123)
        normal_user = User(
            username="user1",
            email="user1@example.com",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyDAXCZ3aKjLXS",
            role="user",
            is_active=True
        )
        db.add(normal_user)

        db.commit()
        print("\n✓ 成功插入初始数据")
        print("  - 管理员用户: admin / admin123")
        print("  - 普通用户: user1 / user123")

    except Exception as e:
        db.rollback()
        print(f"\n✗ 插入初始数据失败: {e}")
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="数据库初始化脚本")
    parser.add_argument("--drop", action="store_true", help="删除并重建所有表")
    parser.add_argument("--with-data", action="store_true", help="创建表并插入初始数据")
    args = parser.parse_args()

    print("=" * 50)
    print("DiskBench Pro 数据库初始化")
    print("=" * 50)

    try:
        create_tables(drop_existing=args.drop)

        if args.with_data:
            insert_initial_data()

        print("\n" + "=" * 50)
        print("数据库初始化完成!")
        print("=" * 50)

    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
