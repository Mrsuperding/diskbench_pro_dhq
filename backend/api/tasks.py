from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from core.database import get_db
from core.security import get_current_user, get_admin_user
from core.websocket import socket_manager
from models.user import User
from models.task import Task, TaskNode, IOPerformanceData, IOStatData, TaskLog
from models.case import TestCase
from models.node import Node, NodePartition
from schemas.task import (
    TaskCreate, 
    TaskUpdate, 
    TaskResponse, 
    TaskListResponse,
    TaskNodeResponse,
    TaskStatusUpdate,
    TaskNodeStatusUpdate,
    IOPerformanceDataCreate,
    IOStatDataCreate,
    TaskLogCreate,
    TaskCloneRequest,
    TaskStatistics
)
from services.task_service import TaskService

from schemas.task import TaskNodeCreate

router = APIRouter()

@router.get("/", response_model=List[TaskListResponse])
async def get_tasks(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务列表"""
    from sqlalchemy.orm import joinedload
    from sqlalchemy import func

    # 使用 joinedload 预加载 test_case 避免 N+1
    query = db.query(Task).options(joinedload(Task.test_case))

    # 普通用户只能看到自己的任务和公开任务
    if current_user.role != "admin":
        query = query.filter(
            (Task.created_by == current_user.id) | (Task.is_public == True)
        )

    # 状态筛选
    if status_filter:
        query = query.filter(Task.status == status_filter)

    tasks = query.offset(skip).limit(limit).all()

    # 一次性获取所有任务的节点数量（子查询）
    task_ids = [t.id for t in tasks]
    node_counts = {}
    if task_ids:
        counts = db.query(
            TaskNode.task_id,
            func.count(TaskNode.id).label('count')
        ).filter(
            TaskNode.task_id.in_(task_ids)
        ).group_by(TaskNode.task_id).all()
        node_counts = {tc.task_id: tc.count for tc in counts}

    # 构建结果
    result = []
    for task in tasks:
        task_data = {
            **task.to_dict(),
            "test_case_name": task.test_case.case_name if task.test_case else "Unknown",
            "node_count": node_counts.get(task.id, 0)
        }
        result.append(task_data)

    return result

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务详情"""
    from sqlalchemy.orm import joinedload, selectinload

    # 预加载关联对象避免 lazy loading 问题
    task = db.query(Task).options(
        joinedload(Task.test_case)
    ).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    # 权限检查
    if current_user.role != "admin" and task.created_by != current_user.id and not task.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此任务"
        )

    return task.to_dict()

@router.post("/", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建任务"""
    # 检查测试用例是否存在
    test_case = db.query(TestCase).filter(TestCase.id == task_data.test_case_id).first()
    if not test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试用例不存在"
        )
    
    # 权限检查 - 测试用例
    if current_user.role != "admin" and test_case.created_by != current_user.id and not test_case.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权使用此测试用例"
        )
    
    # 检查节点是否存在且有权限
    # 构建分区映射（如果未提供，使用节点上第一个可用分区）
    final_partition_mappings = {}
    for node_id in task_data.node_ids:
        node = db.query(Node).filter(Node.id == node_id).first()
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"节点 {node_id} 不存在"
            )

        if current_user.role != "admin" and node.created_by != current_user.id and not node.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无权使用节点 {node_id}"
            )

        # 使用提供的分区映射，或默认使用节点上第一个可用分区
        if node_id in task_data.partition_mappings and task_data.partition_mappings[node_id] > 0:
            partition_id = task_data.partition_mappings[node_id]
        else:
            first_partition = db.query(NodePartition).filter(
                NodePartition.node_id == node_id
            ).first()
            if first_partition:
                partition_id = first_partition.id
            else:
                # 创建默认分区，确保字段与模型匹配
                default_partition = NodePartition(
                    node_id=node_id,
                    partition_name="default",
                    mount_point="/tmp",
                    filesystem="ext4",
                    is_active=True
                )
                db.add(default_partition)
                db.flush()  # 使用 flush 确保立即获取 ID
                partition_id = default_partition.id

        final_partition_mappings[node_id] = partition_id
    
    # 创建任务
    db_task = Task(
        task_name=task_data.task_name,
        description=task_data.description,
        created_by=current_user.id,
        test_case_id=task_data.test_case_id,
        is_public=task_data.is_public
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # 创建任务节点关联
    for node_id in task_data.node_ids:
        db_task_node = TaskNode(
            task_id=db_task.id,
            node_id=node_id,
            partition_id=final_partition_mappings[node_id]
        )
        db.add(db_task_node)
    
    db.commit()

    return db_task.to_dict()

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and task.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此任务"
        )
    
    # 检查名称冲突（如果修改了名称）
    if task_update.task_name and task_update.task_name != task.task_name:
        if db.query(Task).filter(Task.task_name == task_update.task_name).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="任务名称已存在"
            )
    
    # 更新字段
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)

    return task.to_dict()

@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and task.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此任务"
        )
    
    # 只能删除未运行的任务
    if task.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法删除正在运行的任务"
        )
    
    db.delete(task)
    db.commit()
    
    return {"message": "任务删除成功"}

@router.post("/{task_id}/start")
async def start_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """启动任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    task_name = task.task_name
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and task.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此任务"
        )
    
    # 检查任务状态
    if task.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务已在运行中"
        )
    
    # 支持重新运行已完成的任务
    is_restart = task.status == "completed"
    if task.status == "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务已失败，请克隆后重新创建"
        )
    
    # 更新任务状态
    task.status = "running"
    task.start_time = datetime.utcnow()
    task.end_time = None
    task.duration = 0
    
    # 更新任务节点状态
    task_nodes = db.query(TaskNode).filter(TaskNode.task_id == task_id).all()
    for task_node in task_nodes:
        task_node.status = "running"
        task_node.start_time = datetime.utcnow()
        task_node.end_time = None
        task_node.duration = 0
    
    # 如果是重启，清除旧的结果数据
    if is_restart:
        db.query(IOPerformanceData).filter(IOPerformanceData.task_id == task_id).delete()
        db.query(IOStatData).filter(IOStatData.task_id == task_id).delete()
        db.query(TaskLog).filter(TaskLog.task_id == task_id).delete()
        db.commit()
    
    db.commit()
    

    
    # 记录日志
    log_message = f"任务 {task_name} 已重新运行" if is_restart else f"任务 {task_name} 已启动"
    log_entry = TaskLog(
        task_id=task_id,
        log_level="info",
        message=log_message,
        source="system"
    )
    db.add(log_entry)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    
    # 后台执行任务
    # 注意：不要把请求级 db 传给后台任务 —— 请求结束后 get_db 会关闭 session，
    # 后台任务此时再用就会报 "This Session is closed"。
    # TaskService 内部自己用 SessionLocal() 建独立 session。
    task_service = TaskService(socket_manager)
    background_tasks.add_task(task_service.execute_task, task_id)
    
    # WebSocket通知
    await socket_manager.broadcast_to_task(str(task_id), "task_started", {
        "task_id": task_id,
        "task_name": task_name,
        "status": "running",
        "start_time": task.start_time.isoformat()
    })
    
    return {"message": "任务启动成功", "task_id": task_id}

@router.post("/{task_id}/stop")
async def stop_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """停止任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and task.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此任务"
        )
    
    # 检查任务状态
    if task.status != "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务未在运行中"
        )
    
    # 更新任务状态
    task.status = "cancelled"
    task.end_time = datetime.utcnow()
    if task.start_time:
        task.duration = int((task.end_time - task.start_time).total_seconds())
    
    # 更新任务节点状态
    task_nodes = db.query(TaskNode).filter(TaskNode.task_id == task_id).all()
    for task_node in task_nodes:
        if task_node.status == "running":
            task_node.status = "cancelled"
            task_node.end_time = datetime.utcnow()
            if task_node.start_time:
                task_node.duration = int((task_node.end_time - task_node.start_time).total_seconds())
    
    db.commit()
    
    # 记录日志
    log_entry = TaskLog(
        task_id=task_id,
        log_level="info",
        message=f"任务 {task.task_name} 已停止",
        source="system"
    )
    db.add(log_entry)
    db.commit()
    
    # WebSocket通知
    await socket_manager.broadcast_to_task(str(task_id), "task_stopped", {
        "task_id": task_id,
        "task_name": task.task_name,
        "status": "cancelled",
        "end_time": task.end_time.isoformat(),
        "duration": task.duration
    })
    
    return {"message": "任务停止成功", "task_id": task_id}

@router.post("/{task_id}/clone", response_model=TaskResponse)
async def clone_task(
    task_id: int,
    clone_data: TaskCloneRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """克隆任务"""
    original_task = db.query(Task).filter(Task.id == task_id).first()
    if not original_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and original_task.created_by != current_user.id and not original_task.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此任务"
        )
    
    # 检查新名称是否已存在
    if db.query(Task).filter(Task.task_name == clone_data.new_name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务名称已存在"
        )
    
    # 创建克隆任务
    cloned_task = Task(
        task_name=clone_data.new_name,
        description=f"克隆自: {original_task.task_name}\n{original_task.description or ''}",
        created_by=current_user.id,
        test_case_id=original_task.test_case_id,
        is_public=False
    )
    
    db.add(cloned_task)
    db.commit()
    db.refresh(cloned_task)
    
    # 克隆任务节点配置
    original_task_nodes = db.query(TaskNode).filter(TaskNode.task_id == task_id).all()
    for task_node in original_task_nodes:
        cloned_task_node = TaskNode(
            task_id=cloned_task.id,
            node_id=task_node.node_id,
            partition_id=task_node.partition_id
        )
        db.add(cloned_task_node)
    
    db.commit()

    return cloned_task.to_dict()

@router.get("/{task_id}/nodes", response_model=List[TaskNodeResponse])
async def get_task_nodes(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务的节点配置"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and task.created_by != current_user.id and not task.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此任务"
        )
    
    task_nodes = db.query(TaskNode).filter(TaskNode.task_id == task_id).all()
    return [tn.to_dict() for tn in task_nodes]

@router.post("/{task_id}/nodes", response_model=List[TaskNodeResponse])
async def add_task_node(
    task_id: int,
    task_node_data: TaskNodeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """为任务添加节点"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    # 权限检查
    if current_user.role != "admin" and task.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此任务"
        )

    # 检查节点是否存在且有权限
    node = db.query(Node).filter(Node.id == task_node_data.node_id).first()
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点不存在"
        )

    if current_user.role != "admin" and node.created_by != current_user.id and not node.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权使用此节点"
        )

    # 处理分区路径（逗号分隔）
    partition_paths = []
    if task_node_data.partition_path:
        # 解析逗号分隔的分区路径
        partition_paths = [p.strip() for p in task_node_data.partition_path.split(',') if p.strip()]
    elif task_node_data.partition_id:
        # 直接使用 partition_id
        partition_paths = [task_node_data.partition_id]

    # 如果没有提供分区信息，创建一个不带分区的任务节点关联
    if not partition_paths:
        # 检查是否已存在（同一节点无分区）
        existing = db.query(TaskNode).filter(
            TaskNode.task_id == task_id,
            TaskNode.node_id == task_node_data.node_id,
            TaskNode.partition_id.is_(None)
        ).first()
        if existing:
            return [existing.to_dict()]

        # 查找或创建一个占位分区（用于无分区的情况）
        placeholder_partition = db.query(NodePartition).filter(
            NodePartition.node_id == task_node_data.node_id,
            NodePartition.mount_point == "__placeholder__"
        ).first()
        if not placeholder_partition:
            placeholder_partition = NodePartition(
                node_id=task_node_data.node_id,
                partition_name="__placeholder__",
                mount_point="__placeholder__",
                filesystem="unknown"
            )
            db.add(placeholder_partition)
            db.commit()
            db.refresh(placeholder_partition)

        # 创建任务节点（使用占位分区）
        db_task_node = TaskNode(
            task_id=task_id,
            node_id=task_node_data.node_id,
            partition_id=placeholder_partition.id
        )
        db.add(db_task_node)
        db.commit()
        db.refresh(db_task_node)
        return [db_task_node.to_dict()]

    created_nodes = []
    for partition_item in partition_paths:
        # 判断是分区ID还是分区路径
        if isinstance(partition_item, int) or (isinstance(partition_item, str) and partition_item.isdigit()):
            partition_id = int(partition_item)
            partition = db.query(NodePartition).filter(
                NodePartition.id == partition_id,
                NodePartition.node_id == task_node_data.node_id
            ).first()
            if not partition:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"分区不存在 (ID: {partition_id})"
                )
        else:
            # 按分区路径查找或创建
            partition = db.query(NodePartition).filter(
                NodePartition.mount_point == partition_item,
                NodePartition.node_id == task_node_data.node_id
            ).first()
            if not partition:
                # 创建新分区
                partition = NodePartition(
                    node_id=task_node_data.node_id,
                    partition_name=partition_item,
                    mount_point=partition_item,
                    filesystem="unknown"
                )
                db.add(partition)
                db.commit()
                db.refresh(partition)

        # 检查是否已存在（同一节点+同一分区）
        existing = db.query(TaskNode).filter(
            TaskNode.task_id == task_id,
            TaskNode.node_id == task_node_data.node_id,
            TaskNode.partition_id == partition.id
        ).first()

        if existing:
            continue  # 跳过已存在的

        # 创建任务节点
        db_task_node = TaskNode(
            task_id=task_id,
            node_id=task_node_data.node_id,
            partition_id=partition.id
        )
        db.add(db_task_node)
        created_nodes.append(db_task_node)

    db.commit()
    for tn in created_nodes:
        db.refresh(tn)

    return [tn.to_dict() for tn in created_nodes]

@router.delete("/{task_id}/nodes/{node_id}")
async def remove_task_node(
    task_id: int,
    node_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """从任务中移除节点"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and task.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此任务"
        )
    
    # 检查任务状态
    if task.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法修改正在运行的任务"
        )
    
    task_node = db.query(TaskNode).filter(
        TaskNode.task_id == task_id,
        TaskNode.node_id == node_id
    ).first()
    
    if not task_node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务节点不存在"
        )
    
    db.delete(task_node)
    db.commit()
    
    return {"message": "任务节点移除成功"}

# 性能数据相关接口
@router.post("/{task_id}/performance-data")
async def add_performance_data(
    task_id: int,
    task_node_id: int,
    performance_data: IOPerformanceDataCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加性能数据（内部使用）"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    task_node = db.query(TaskNode).filter(
        TaskNode.id == task_node_id,
        TaskNode.task_id == task_id
    ).first()
    
    if not task_node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务节点不存在"
        )
    
    db_performance = IOPerformanceData(
        task_node_id=task_node_id,
        **performance_data.dict()
    )
    
    db.add(db_performance)
    db.commit()
    db.refresh(db_performance)
    
    return db_performance

@router.get("/{task_id}/performance-data")
async def get_performance_data(
    task_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务性能数据"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and task.created_by != current_user.id and not task.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此任务"
        )
    
    # 查询性能数据
    query = db.query(IOPerformanceData).join(TaskNode).filter(
        TaskNode.task_id == task_id
    )
    
    if start_time:
        query = query.filter(IOPerformanceData.timestamp >= start_time)
    
    if end_time:
        query = query.filter(IOPerformanceData.timestamp <= end_time)
    
    performance_data = query.order_by(IOPerformanceData.timestamp.asc()).all()
    
    return [data.to_dict() for data in performance_data]

# 日志相关接口
@router.get("/{task_id}/logs")
async def get_task_logs(
    task_id: int,
    log_level: Optional[str] = None,
    limit: int = 1000,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务日志"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and task.created_by != current_user.id and not task.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此任务"
        )
    
    query = db.query(TaskLog).filter(TaskLog.task_id == task_id)
    
    if log_level:
        query = query.filter(TaskLog.log_level == log_level)
    
    logs = query.order_by(TaskLog.created_at.desc()).limit(limit).all()
    
    return [log.to_dict() for log in logs]

@router.post("/{task_id}/logs")
async def add_task_log(
    task_id: int,
    log_data: TaskLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加任务日志"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 权限检查
    if current_user.role != "admin" and task.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此任务"
        )
    
    db_log = TaskLog(
        task_id=task_id,
        **log_data.dict()
    )
    
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    
    return db_log

# 统计接口
@router.get("/statistics/", response_model=TaskStatistics)
async def get_task_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务统计信息"""
    query = db.query(Task)
    
    # 普通用户只能看到自己的统计
    if current_user.role != "admin":
        query = query.filter(Task.created_by == current_user.id)
    
    tasks = query.all()
    
    total_tasks = len(tasks)
    running_tasks = sum(1 for task in tasks if task.status == "running")
    completed_tasks = sum(1 for task in tasks if task.status == "completed")
    failed_tasks = sum(1 for task in tasks if task.status == "failed")
    
    # 计算平均持续时间
    completed_task_durations = [task.duration for task in tasks if task.status == "completed" and task.duration > 0]
    avg_duration = sum(completed_task_durations) / len(completed_task_durations) if completed_task_durations else 0
    
    # 总IO操作数
    total_io_ops = sum(task.total_io_ops for task in tasks)
    
    return TaskStatistics(
        total_tasks=total_tasks,
        running_tasks=running_tasks,
        completed_tasks=completed_tasks,
        failed_tasks=failed_tasks,
        avg_duration=avg_duration,
        total_io_ops=total_io_ops
    )
