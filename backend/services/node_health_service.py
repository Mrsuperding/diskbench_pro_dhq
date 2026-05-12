"""
节点健康检查服务
================
核心功能：
1. 周期性地对所有节点做 SSH 连通性测试
2. 根据结果自动更新节点状态（online/offline/testing）
3. 连续失败超过阈值标红，通过 WebSocket 通知前端
4. 支持单节点立即复查（手动触发）

使用：
    # 在 main.py 启动时
    from services.node_health_service import node_health_service
    asyncio.create_task(node_health_service.start_loop(socket_manager))

    # 停止（主要用于测试）
    await node_health_service.stop()
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from core.database import SessionLocal
from models.node import Node
from services.ssh_service import SSHService


# 健康检查参数（可通过环境变量或配置调整）
_CHECK_INTERVAL_SEC = 60         # 每轮检查间隔
_CHECK_TIMEOUT_SEC = 8           # 单个节点 SSH 握手超时
_OFFLINE_THRESHOLD = 3           # 连续失败 N 次标为 offline


class NodeHealthService:
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._stopped = asyncio.Event()
        self._in_progress = False  # 简单锁防并发
        self._socket_mgr = None

    # ------------------------------------------------------------- 生命周期 ----

    async def start_loop(self, socket_mgr=None):
        """启动周期性健康检查"""
        self._socket_mgr = socket_mgr
        self._stopped.clear()
        self._task = asyncio.create_task(self._run())

    async def stop(self):
        self._stopped.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run(self):
        """主循环"""
        # 启动后先等几秒，让数据库就绪
        await asyncio.sleep(5)
        while not self._stopped.is_set():
            try:
                await self.check_all_nodes()
            except Exception as e:
                print(f"[health] check cycle error: {e}")
            # 用 wait_for 让 stop 可以立即中断等待
            try:
                await asyncio.wait_for(self._stopped.wait(), timeout=_CHECK_INTERVAL_SEC)
            except asyncio.TimeoutError:
                pass

    # -------------------------------------------------------------- 核心检查 ----

    async def check_all_nodes(self):
        """遍历所有启用的节点，并发检查"""
        if self._in_progress:
            # 上一轮还没结束，本轮跳过（避免 SSH 连接数暴涨）
            return
        self._in_progress = True
        try:
            db: Session = SessionLocal()
            try:
                nodes = db.query(Node).all()
                node_ids = [n.id for n in nodes]
            finally:
                db.close()

            if not node_ids:
                return

            # 并发检查，但限制并发度，避免同时建太多 SSH
            sem = asyncio.Semaphore(10)

            async def _limited_check(nid):
                async with sem:
                    await self._check_one_node(nid)

            await asyncio.gather(
                *[_limited_check(nid) for nid in node_ids],
                return_exceptions=True,
            )
        finally:
            self._in_progress = False

    async def _check_one_node(self, node_id: int) -> bool:
        """
        检查单个节点连通性
        Returns: True=online / False=offline
        """
        db: Session = SessionLocal()
        try:
            node = db.query(Node).filter(Node.id == node_id).first()
            if not node:
                return False

            # 记录指纹快照用于 WebSocket 通知（避免在后续事务里重新查一遍）
            old_status = node.status

            ssh = SSHService()
            ok = await ssh.test_connection(
                host=node.host,
                port=node.port,
                username=node.username,
                password=node.password,
                private_key=node.private_key,
                timeout=_CHECK_TIMEOUT_SEC,
            )

            now = datetime.utcnow()
            node.last_health_check_at = now

            if ok:
                node.status = "online"
                node.last_online_at = now
                node.health_fail_count = 0
                node.health_message = None
            else:
                node.health_fail_count = (node.health_fail_count or 0) + 1
                node.health_message = "SSH 连接失败"
                # 连续失败超过阈值再真正标为 offline，避免偶发网络波动
                if node.health_fail_count >= _OFFLINE_THRESHOLD:
                    node.status = "offline"

            db.commit()

            # 状态发生变化时推送给前端
            if old_status != node.status and self._socket_mgr is not None:
                try:
                    await self._socket_mgr.broadcast("node_status_changed", {
                        "node_id": node.id,
                        "node_name": node.node_name,
                        "status": node.status,
                        "health_fail_count": node.health_fail_count,
                        "health_message": node.health_message,
                        "timestamp": now.isoformat(),
                    })
                except Exception as e:
                    print(f"[health] broadcast error: {e}")

            return ok
        except Exception as e:
            print(f"[health] check node {node_id} error: {e}")
            return False
        finally:
            db.close()

    async def recheck_node(self, node_id: int) -> dict:
        """
        手动触发某节点的立即复查（给 API 用）
        Returns: {node_id, status, checked_at, message}
        """
        ok = await self._check_one_node(node_id)
        db = SessionLocal()
        try:
            node = db.query(Node).filter(Node.id == node_id).first()
            if not node:
                return {"ok": False, "message": "node not found"}
            return {
                "ok": ok,
                "node_id": node.id,
                "status": node.status,
                "checked_at": node.last_health_check_at.isoformat() if node.last_health_check_at else None,
                "message": node.health_message,
                "fail_count": node.health_fail_count,
            }
        finally:
            db.close()


# 全局单例
node_health_service = NodeHealthService()
