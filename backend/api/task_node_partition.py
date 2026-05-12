"""
任务节点分区关联 API
====================
提供任务节点分区关联和百分位数数据管理的 API 端点。
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database import get_db
from core.security import get_current_user
from models.task import Task, TaskNode
from models.task_node_partition import TaskNodePartition, TestResultPercentile
from models.node import Node, NodePartition
from models.user import User

router = APIRouter()


# ============== TaskNodePartition Endpoints ==============

@router.get("/task-node-partitions/", response_model=List[dict])
async def get_task_node_partitions(
    task_id: Optional[int] = None,
    node_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务节点分区关联列表"""
    query = db.query(TaskNodePartition)

    if task_id:
        query = query.filter(TaskNodePartition.task_id == task_id)
    if node_id:
        query = query.filter(TaskNodePartition.node_id == node_id)

    partitions = query.offset(skip).limit(limit).all()
    return [p.to_dict() for p in partitions]


@router.get("/task-node-partitions/{partition_id}", response_model=dict)
async def get_task_node_partition(
    partition_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个任务节点分区关联详情"""
    partition = db.query(TaskNodePartition).filter(
        TaskNodePartition.id == partition_id
    ).first()

    if not partition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务节点分区关联不存在"
        )

    return partition.to_dict()


@router.post("/task-node-partitions", response_model=dict)
async def create_task_node_partition(
    task_id: int,
    node_id: int,
    partition_id: int,
    capacity_limit: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建任务节点分区关联"""
    # 验证任务存在
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    # 验证节点存在
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点不存在"
        )

    # 验证分区存在且属于该节点
    partition = db.query(NodePartition).filter(
        NodePartition.id == partition_id,
        NodePartition.node_id == node_id
    ).first()
    if not partition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分区不存在或不属于该节点"
        )

    # 检查是否已存在
    existing = db.query(TaskNodePartition).filter(
        TaskNodePartition.task_id == task_id,
        TaskNodePartition.node_id == node_id,
        TaskNodePartition.partition_id == partition_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该任务节点分区关联已存在"
        )

    db_partition = TaskNodePartition(
        task_id=task_id,
        node_id=node_id,
        partition_id=partition_id,
        capacity_limit=capacity_limit
    )

    db.add(db_partition)
    db.commit()
    db.refresh(db_partition)

    return db_partition.to_dict()


@router.put("/task-node-partitions/{partition_id}", response_model=dict)
async def update_task_node_partition(
    partition_id: int,
    capacity_limit: Optional[int] = None,
    init_status: Optional[str] = None,
    status: Optional[str] = None,
    error_message: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新任务节点分区关联"""
    partition = db.query(TaskNodePartition).filter(
        TaskNodePartition.id == partition_id
    ).first()

    if not partition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务节点分区关联不存在"
        )

    if capacity_limit is not None:
        partition.capacity_limit = capacity_limit
    if init_status is not None:
        partition.init_status = init_status
    if status is not None:
        partition.status = status
    if error_message is not None:
        partition.error_message = error_message

    db.commit()
    db.refresh(partition)

    return partition.to_dict()


@router.delete("/task-node-partitions/{partition_id}")
async def delete_task_node_partition(
    partition_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除任务节点分区关联"""
    partition = db.query(TaskNodePartition).filter(
        TaskNodePartition.id == partition_id
    ).first()

    if not partition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务节点分区关联不存在"
        )

    db.delete(partition)
    db.commit()

    return {"message": "删除成功"}


@router.post("/task-node-partitions/batch", response_model=List[dict])
async def create_task_node_partitions_batch(
    items: List[dict],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量创建任务节点分区关联"""
    results = []
    for item in items:
        task_id = item.get("task_id")
        node_id = item.get("node_id")
        partition_id = item.get("partition_id")
        capacity_limit = item.get("capacity_limit", 0)

        # 验证任务存在
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            continue

        # 验证分区
        partition = db.query(NodePartition).filter(
            NodePartition.id == partition_id,
            NodePartition.node_id == node_id
        ).first()
        if not partition:
            continue

        # 检查是否已存在
        existing = db.query(TaskNodePartition).filter(
            TaskNodePartition.task_id == task_id,
            TaskNodePartition.node_id == node_id,
            TaskNodePartition.partition_id == partition_id
        ).first()
        if existing:
            results.append(existing.to_dict())
            continue

        db_partition = TaskNodePartition(
            task_id=task_id,
            node_id=node_id,
            partition_id=partition_id,
            capacity_limit=capacity_limit
        )
        db.add(db_partition)
        results.append(db_partition)

    db.commit()
    for p in results:
        if isinstance(p, TaskNodePartition):
            db.refresh(p)

    return [p.to_dict() if hasattr(p, 'to_dict') else p for p in results]


# ============== TestResultPercentile Endpoints ==============

@router.get("/task-nodes/{task_node_id}/percentiles", response_model=List[dict])
async def get_task_node_percentiles(
    task_node_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务节点的百分位数数据"""
    # 验证 task_node 存在
    task_node = db.query(TaskNode).filter(TaskNode.id == task_node_id).first()
    if not task_node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务节点不存在"
        )

    percentiles = db.query(TestResultPercentile).filter(
        TestResultPercentile.task_node_id == task_node_id
    ).all()

    return [p.to_dict() for p in percentiles]


@router.post("/task-nodes/{task_node_id}/percentiles", response_model=List[dict])
async def create_task_node_percentiles(
    task_node_id: int,
    items: List[dict],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量创建任务节点的百分位数数据"""
    # 验证 task_node 存在
    task_node = db.query(TaskNode).filter(TaskNode.id == task_node_id).first()
    if not task_node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务节点不存在"
        )

    # 删除旧数据
    db.query(TestResultPercentile).filter(
        TestResultPercentile.task_node_id == task_node_id
    ).delete()

    # 创建新数据
    results = []
    for item in items:
        db_percentile = TestResultPercentile(
            task_node_id=task_node_id,
            percentile_name=item.get("percentile_name"),
            latency_us=item.get("latency_us"),
            test_type=item.get("test_type")
        )
        db.add(db_percentile)
        results.append(db_percentile)

    db.commit()
    for p in results:
        db.refresh(p)

    return [p.to_dict() for p in results]