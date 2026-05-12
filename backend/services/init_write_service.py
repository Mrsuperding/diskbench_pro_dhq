"""
初始化写入服务
==============
在 IO 测试之前执行初始化写入，确保测试数据在磁盘上真实存在。

初始化写入参数：
- rw=write
- bs=1M
- iodepth=32
- numjobs=1
- size=<capacity_limit> 或分区可用空间

所有节点/分区并发初始化，失败的分区标记为不可用，任务继续执行。
"""
import asyncio
import shlex
from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from core.database import SessionLocal
from models.task import Task, TaskNode, TaskLog
from models.task_node_partition import TaskNodePartition
from services.ssh_service import SSHService


class InitWriteService:
    """
    初始化写入服务

    在 IO 测试开始前，对所有节点-分区对执行初始化写入。
    使用 fio 顺序写入来初始化测试区域，确保后续测试的数据在磁盘真实位置上。
    """

    def __init__(self, socket_manager):
        self.socket_manager = socket_manager

    async def execute_init_write(
        self,
        task_id: int,
        task_node_partition_ids: List[int] = None
    ) -> Dict[int, bool]:
        """
        执行初始化写入

        Args:
            task_id: 任务ID
            task_node_partition_ids: 可选，指定要初始化的 TaskNodePartition IDs
                                    如果为 None，则初始化任务的所有分区

        Returns:
            Dict[node_partition_id, success]: 每个分区的初始化结果
        """
        db = SessionLocal()
        results = {}

        try:
            # 获取任务节点分区关联
            if task_node_partition_ids:
                tnp_query = db.query(TaskNodePartition).filter(
                    TaskNodePartition.id.in_(task_node_partition_ids)
                )
            else:
                tnp_query = db.query(TaskNodePartition).filter(
                    TaskNodePartition.task_id == task_id
                )

            task_node_partitions = tnp_query.all()

            # 并发执行所有分区的初始化
            coros = [
                self._init_single_partition(db, task_id, tnp)
                for tnp in task_node_partitions
            ]
            partition_results = await asyncio.gather(*coros, return_exceptions=True)

            # 收集结果
            for tnp, result in zip(task_node_partitions, partition_results):
                if isinstance(result, Exception):
                    results[tnp.id] = False
                else:
                    results[tnp.id] = result

        except Exception as e:
            await self._log_error(db, task_id, f"初始化写入服务异常: {e!s}")
        finally:
            db.close()

        return results

    async def _init_single_partition(
        self,
        db: Session,
        task_id: int,
        tnp: TaskNodePartition
    ) -> bool:
        """
        初始化单个分区

        Returns:
            True: 成功
            False: 失败
        """
        ssh_service: Optional[SSHService] = None

        try:
            # 更新状态为 running
            tnp.init_status = "running"
            tnp.init_start_time = datetime.utcnow()
            db.commit()

            await self._log_info(
                db, task_id,
                f"开始初始化分区 {tnp.partition.partition_name} "
                f"on node {tnp.node.node_name}"
            )

            # 获取 SSH 连接
            node = tnp.node
            ssh_service = SSHService()
            ok = await ssh_service.connect(
                host=node.host,
                port=node.port,
                username=node.username,
                password=node.password,
                private_key=node.private_key,
            )

            if not ok:
                tnp.init_status = "failed"
                tnp.init_error = "SSH 连接失败"
                tnp.init_end_time = datetime.utcnow()
                db.commit()
                await self._log_error(
                    db, task_id,
                    f"节点 {node.node_name} SSH 连接失败"
                )
                return False

            # 确定初始化大小
            if tnp.capacity_limit > 0:
                init_size = f"{tnp.capacity_limit}M"
            else:
                # 使用分区可用空间
                partition = tnp.partition
                if partition.available_size and partition.available_size > 0:
                    # 使用 80% 的可用空间，避免占满
                    init_size_mb = int(partition.available_size * 0.8)
                    init_size = f"{init_size_mb}M"
                else:
                    init_size = "1G"  # 默认 1GB

            # 生成 fio 初始化命令
            # 使用顺序写入 (rw=write), block_size=1M, iodepth=32, numjobs=1
            test_file = f"{tnp.partition.mount_point}/.diskbench_init_{tnp.id}.dat"
            fio_cmd = (
                f"fio --name=init_write "
                f"--rw=write "
                f"--bs=1M "
                f"--iodepth=32 "
                f"--numjobs=1 "
                f"--size={init_size} "
                f"--filename={shlex.quote(test_file)} "
                f"--ioengine=libaio "
                f"--direct=1 "
                f"--runtime=300 "  # 最多运行 5 分钟
                f"--time_based=0 "  # 达到大小就停止
                f"--group_reporting=1"
            )

            await self._log_info(db, task_id, f"执行初始化写入: {fio_cmd}")

            # 执行 fio（带超时）
            result = await ssh_service.execute_command(fio_cmd, timeout=360)

            if not result.get("success"):
                tnp.init_status = "failed"
                tnp.init_error = result.get("stderr") or result.get("error") or "初始化写入失败"
                tnp.init_end_time = datetime.utcnow()
                db.commit()
                await self._log_error(
                    db, task_id,
                    f"分区 {tnp.partition.partition_name} 初始化写入失败: {tnp.init_error}"
                )
                return False

            # 清理初始化文件
            await ssh_service.execute_command(
                f"rm -f {shlex.quote(test_file)}",
                timeout=30
            )

            # 更新状态为 completed
            tnp.init_status = "completed"
            tnp.init_end_time = datetime.utcnow()
            db.commit()

            await self._log_info(
                db, task_id,
                f"分区 {tnp.partition.partition_name} 初始化完成"
            )

            # 通知 WebSocket
            await self.socket_manager.broadcast_to_task(
                str(task_id),
                "init_write_progress",
                {
                    "partition_id": tnp.id,
                    "node_name": node.node_name,
                    "partition_name": tnp.partition.partition_name,
                    "status": "completed"
                }
            )

            return True

        except asyncio.TimeoutError:
            tnp.init_status = "failed"
            tnp.init_error = "初始化写入超时 (360秒)"
            tnp.init_end_time = datetime.utcnow()
            db.commit()
            await self._log_error(
                db, task_id,
                f"分区 {tnp.partition.partition_name} 初始化写入超时"
            )
            return False

        except Exception as e:
            tnp.init_status = "failed"
            tnp.init_error = str(e)
            tnp.init_end_time = datetime.utcnow()
            db.commit()
            await self._log_error(
                db, task_id,
                f"分区 {tnp.partition.partition_name} 初始化写入异常: {e!s}"
            )
            return False

        finally:
            if ssh_service:
                ssh_service.close()

    async def _log_info(self, db: Session, task_id: int, msg: str):
        await self._add_log(db, task_id, "info", msg)

    async def _log_error(self, db: Session, task_id: int, msg: str):
        await self._add_log(db, task_id, "error", msg)

    async def _add_log(self, db: Session, task_id: int, level: str, message: str):
        entry = TaskLog(task_id=task_id, log_level=level, message=message, source="init_write")
        db.add(entry)
        db.commit()
        try:
            await self.socket_manager.broadcast_to_task(
                str(task_id),
                "log_update",
                {
                    "level": level,
                    "message": message,
                    "source": "init_write",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except Exception:
            pass