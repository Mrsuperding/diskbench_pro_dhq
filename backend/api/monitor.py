# -*- coding: utf-8 -*-
"""
系统监控相关接口
- 磁盘/内存/CPU 采样
- 实时曲线数据推送（WebSocket 预留）
- 节点分区性能监控
"""
from fastapi import APIRouter, WebSocket, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import asyncio
import psutil
import time
import uuid

from core.database import Base, get_db, SessionLocal
from core.websocket import socket_manager
from models.monitor import Monitor
from models.node import Node, NodePartition
from services.ssh_service import SSHService
from pydantic import BaseModel

router = APIRouter(tags=["monitor"])


# -------------------- 响应模型 --------------------
class SampleOut(BaseModel):
    ts: int  # 时间戳(秒)
    cpu: float  # 使用率 %
    mem: float  # 内存使用率 %
    disk: float  # 主磁盘使用率 %


# -------------------- REST 接口 --------------------
@router.get("/sample", response_model=SampleOut, summary="瞬时采样")
def sample():
    return SampleOut(
        ts=int(datetime.now().timestamp()),
        cpu=psutil.cpu_percent(interval=0.5),
        mem=psutil.virtual_memory().percent,
        disk=psutil.disk_usage("/").percent,
    )


# -------------------- WebSocket 推送 --------------------
class ConnManager:
    """简易连接池，后续可迁到公共模块"""

    def __init__(self):
        # 使用 List 注解以兼容 Python 3.8
        self.active: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        # 原来直接 remove，ws 不在列表时会抛 ValueError
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, msg: str):
        # 并发发送，异常隔离
        await asyncio.gather(
            *[ws.send_text(msg) for ws in self.active],
            return_exceptions=True,
        )


ws_mgr = ConnManager()


@router.websocket("/ws")
async def monitor_ws(websocket: WebSocket):
    """
    简单的系统监控 WebSocket
    修复：
    - 裸 except 吞掉所有异常（包括 KeyboardInterrupt）
    - psutil.cpu_percent() 无间隔第一次调用返回 0
    - 无异常也要在客户端断开时清理连接池
    """
    await websocket.accept()
    # 首次调用 cpu_percent(interval=None) 总返回 0，这里先预热一下
    psutil.cpu_percent(interval=None)
    try:
        while True:
            await asyncio.sleep(2)
            data = {
                "ts": time.strftime("%H:%M:%S"),
                "cpu": psutil.cpu_percent(interval=None),
                "mem": psutil.virtual_memory().percent,
                "disk": psutil.disk_usage("/").percent,
            }
            await websocket.send_json(data)
    except Exception as e:
        # 日志化，避免整吞
        print(f"[monitor_ws] client disconnected: {e}")
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


class MonitorOut(BaseModel):
    id: int
    ts: datetime
    cpu: float
    mem: float
    disk: float

    # Pydantic v2
    model_config = {"from_attributes": True}


@router.get("/history", response_model=list[MonitorOut])
def history(hours: int = 24, db: Session = Depends(get_db)):
    since = datetime.utcnow() - timedelta(hours=hours)
    return db.query(Monitor).filter(Monitor.created_at >= since).all()


# ==================== 节点分区监控 API ====================

# -------------------- 请求/响应模型 --------------------
class PartitionMonitorStart(BaseModel):
    node_id: int
    partition_ids: List[int]  # 分区ID列表
    interval: int = 1  # 采集间隔（秒）


class PartitionMonitorStop(BaseModel):
    monitor_id: str


class PartitionMonitorResponse(BaseModel):
    monitor_id: str
    status: str
    node_id: int
    partitions: List[Dict[str, Any]]


class PartitionPerformanceData(BaseModel):
    monitor_id: str
    node_id: int
    partition_id: int
    device: str
    mount_point: str
    timestamp: str
    iops: float
    read_iops: float
    write_iops: float
    bw_mbs: float
    read_bw_mbs: float
    write_bw_mbs: float
    latency_ms: float
    util_percent: float


# -------------------- 节点分区监控服务 --------------------
class NodePartitionMonitorService:
    """节点分区监控服务"""

    def __init__(self):
        self.active_monitors: Dict[str, Dict[str, Any]] = {}
        self.monitor_tasks: Dict[str, List[asyncio.Task]] = {}

    async def start_monitor(
        self,
        monitor_id: str,
        node_id: int,
        partitions: List[Dict[str, Any]],
        interval: int,
        socket_mgr
    ) -> bool:
        """启动分区监控"""
        if monitor_id in self.active_monitors:
            return False

        # 建立 SSH 连接
        db = SessionLocal()
        try:
            node = db.query(Node).filter(Node.id == node_id).first()
            if not node:
                return False

            ssh_service = SSHService()
            connected = await ssh_service.connect(
                host=node.host,
                port=node.port,
                username=node.username,
                password=node.password,
                private_key=node.private_key
            )

            if not connected:
                return False

            # 保存监控状态
            self.active_monitors[monitor_id] = {
                "node_id": node_id,
                "partitions": partitions,
                "interval": interval,
                "ssh_service": ssh_service,
                "start_time": datetime.utcnow(),
                "status": "running"
            }

            # 创建采集任务
            self.monitor_tasks[monitor_id] = []
            for partition in partitions:
                task = asyncio.create_task(
                    self._monitor_partition(
                        monitor_id, node_id, partition, interval, socket_mgr
                    )
                )
                self.monitor_tasks[monitor_id].append(task)

            return True

        finally:
            db.close()

    async def stop_monitor(self, monitor_id: str) -> bool:
        """停止分区监控"""
        if monitor_id not in self.active_monitors:
            return False

        # 取消所有采集任务并等待它们退出
        if monitor_id in self.monitor_tasks:
            tasks = self.monitor_tasks[monitor_id]
            for task in tasks:
                task.cancel()
            # 等待所有任务真正退出，避免后面 close SSH 时任务还在用
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            del self.monitor_tasks[monitor_id]

        # 关闭 SSH 连接（使用封装好的 close 方法）
        ssh_service = self.active_monitors[monitor_id].get("ssh_service")
        if ssh_service:
            try:
                ssh_service.close()
            except Exception:
                pass

        # 删除监控状态
        del self.active_monitors[monitor_id]

        return True

    async def _monitor_partition(
        self,
        monitor_id: str,
        node_id: int,
        partition: Dict[str, Any],
        interval: int,
        socket_mgr
    ):
        """监控单个分区"""
        partition_id = partition["id"]
        device = partition["device"]
        mount_point = partition["mount_point"]

        ssh_service = self.active_monitors[monitor_id]["ssh_service"]

        while True:
            try:
                # 获取分区 iostat 数据
                result = await ssh_service.get_partition_iostat(device, interval)

                if result.get("success"):
                    data = {
                        "monitor_id": monitor_id,
                        "node_id": node_id,
                        "partition_id": partition_id,
                        "device": device,
                        "mount_point": mount_point,
                        "timestamp": datetime.utcnow().isoformat(),
                        "iops": result.get("total_iops", 0),
                        "read_iops": result.get("read_iops", 0),
                        "write_iops": result.get("write_iops", 0),
                        "bw_mbs": result.get("total_bw_mbs", 0),
                        "read_bw_mbs": result.get("read_bw_mbs", 0),
                        "write_bw_mbs": result.get("write_bw_mbs", 0),
                        "latency_ms": result.get("await_ms", 0),
                        "util_percent": result.get("util_percent", 0),
                    }

                    # 通过 WebSocket 广播
                    await socket_mgr.broadcast_to_node_partition(
                        monitor_id, "partition_performance_data", data
                    )

                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Monitor partition error: {e}")
                await asyncio.sleep(interval)

    def get_monitor_status(self, monitor_id: str) -> Optional[Dict[str, Any]]:
        """获取监控状态"""
        return self.active_monitors.get(monitor_id)

    def list_monitors(self) -> Dict[str, Dict[str, Any]]:
        """列出所有监控"""
        return self.active_monitors.copy()


# 全局监控服务实例
partition_monitor_service = NodePartitionMonitorService()


# -------------------- REST API --------------------

@router.post("/node/partition/start", response_model=PartitionMonitorResponse)
async def start_partition_monitor(
    request: PartitionMonitorStart,
    db: Session = Depends(get_db)
):
    """开始节点分区监控"""
    # 获取节点信息
    node = db.query(Node).filter(Node.id == request.node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail=f"Node {request.node_id} not found")

    if node.status != "online":
        raise HTTPException(status_code=400, detail=f"Node {request.node_id} is not online")

    # 修复：每个分区都新建 SSH 连接既浪费也会泄漏；改成只建一次连接
    # 并用 try/finally 确保一定关闭
    partitions = []
    ssh_service = SSHService()
    try:
        connected = await ssh_service.connect(
            host=node.host,
            port=node.port,
            username=node.username,
            password=node.password,
            private_key=node.private_key,
        )
        if not connected:
            raise HTTPException(status_code=503,
                                detail=f"Failed to SSH into node {request.node_id}")

        for partition_id in request.partition_ids:
            partition = db.query(NodePartition).filter(
                NodePartition.id == partition_id,
                NodePartition.node_id == request.node_id,
            ).first()
            if not partition:
                continue
            device = await ssh_service.get_device_by_mountpoint(partition.mount_point)
            if device:
                partitions.append({
                    "id": partition.id,
                    "device": device,
                    "mount_point": partition.mount_point,
                    "partition_name": partition.partition_name,
                })
    finally:
        # 修复：原代码只有 connected 且 get_device_by_mountpoint 成功时才 close，
        # 其他路径都会泄漏；这里确保一定关闭
        ssh_service.close()

    if not partitions:
        raise HTTPException(status_code=400, detail="No valid partitions found")

    # 生成监控ID
    monitor_id = str(uuid.uuid4())[:8]

    # 启动监控
    success = await partition_monitor_service.start_monitor(
        monitor_id=monitor_id,
        node_id=request.node_id,
        partitions=partitions,
        interval=request.interval,
        socket_mgr=socket_manager
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to start partition monitor")

    return PartitionMonitorResponse(
        monitor_id=monitor_id,
        status="started",
        node_id=request.node_id,
        partitions=partitions
    )


@router.post("/node/partition/stop")
async def stop_partition_monitor(request: PartitionMonitorStop):
    """停止节点分区监控"""
    success = await partition_monitor_service.stop_monitor(request.monitor_id)

    if not success:
        raise HTTPException(status_code=404,
                            detail=f"Monitor {request.monitor_id} not found or already stopped")

    return {"monitor_id": request.monitor_id, "status": "stopped"}


@router.get("/node/partition/monitors")
async def list_partition_monitors():
    """列出所有活动监控"""
    monitors = partition_monitor_service.list_monitors()

    result = []
    for monitor_id, info in monitors.items():
        result.append({
            "monitor_id": monitor_id,
            "node_id": info["node_id"],
            "partitions_count": len(info["partitions"]),
            "interval": info["interval"],
            "start_time": info["start_time"].isoformat(),
            "status": info["status"]
        })

    return result


@router.get("/node/partition/{monitor_id}/status")
async def get_partition_monitor_status(monitor_id: str):
    """获取指定监控状态"""
    info = partition_monitor_service.get_monitor_status(monitor_id)

    if not info:
        return {"monitor_id": monitor_id, "status": "not_found"}

    return {
        "monitor_id": monitor_id,
        "node_id": info["node_id"],
        "partitions": info["partitions"],
        "interval": info["interval"],
        "start_time": info["start_time"].isoformat(),
        "status": info["status"]
    }
