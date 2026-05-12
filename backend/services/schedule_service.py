"""
调度服务
========
轻量级调度器，每 30 秒扫一次所有启用中的 ScheduledTask，
判断当前时间是否到达 next_run_at；到了就克隆一个任务实例并提交执行。

为什么不用 APScheduler/Celery Beat：
  - 这个项目已经是 asyncio FastAPI，引入 APScheduler 会带来额外依赖和进程模型复杂度
  - 调度逻辑非常简单（三种触发，分钟粒度够用），直接实现反而清晰
  - 状态全部持久化在数据库，重启不会丢调度任务

实现要点：
  - 每轮扫描用独立 SessionLocal，不会影响请求线程
  - 一次扫描最多触发若干任务（limit），避免大量积压
  - 克隆 Task/TaskNode 时保留同一 test_case 和 partition 配置
  - 用 ScheduledTask.run_count 做失效保护：interval 类型跑完 end_at 后自动关闭
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy.orm import Session

from core.database import SessionLocal
from models.schedule import ScheduledTask
from models.task import Task, TaskNode


_SCAN_INTERVAL_SEC = 30  # 扫描间隔


class ScheduleService:
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._stopped = asyncio.Event()
        self._socket_mgr = None
        self._task_service_factory = None

    def start(self, socket_mgr, task_service_factory):
        """
        Args:
            socket_mgr: WebSocket 广播器
            task_service_factory: callable -> TaskService 实例
                调度器触发时通过它拿到 TaskService 并调用 execute_task
        """
        self._socket_mgr = socket_mgr
        self._task_service_factory = task_service_factory
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
        await asyncio.sleep(10)  # 等数据库就绪
        while not self._stopped.is_set():
            try:
                await self._tick()
            except Exception as e:
                print(f"[schedule] tick error: {e}")
            try:
                await asyncio.wait_for(self._stopped.wait(), timeout=_SCAN_INTERVAL_SEC)
            except asyncio.TimeoutError:
                pass

    # ------------------------------------------------------------ 调度主循环 ----

    async def _tick(self):
        """一轮扫描"""
        now = datetime.utcnow()
        db = SessionLocal()
        try:
            # 只处理 enabled 且 next_run_at <= now 的调度
            due: List[ScheduledTask] = (
                db.query(ScheduledTask)
                .filter(ScheduledTask.enabled == True)   # noqa: E712
                .filter(
                    (ScheduledTask.next_run_at.is_(None))
                    | (ScheduledTask.next_run_at <= now)
                )
                .limit(50)
                .all()
            )

            for sched in due:
                await self._fire(db, sched, now)
        finally:
            db.close()

    async def _fire(self, db: Session, sched: ScheduledTask, now: datetime):
        """触发一次调度"""
        # 算下次执行时间
        next_at = self._compute_next_run(sched, now)

        # 对于 once 类型，触发后关闭
        if sched.trigger_type == "once":
            sched.enabled = False

        # 对于 interval，如果超过 end_at 也关闭
        if sched.trigger_type == "interval" and sched.end_at and now >= sched.end_at:
            sched.enabled = False

        try:
            new_task_id = self._clone_task(db, sched.template_task_id, sched)
            if new_task_id is None:
                sched.last_run_status = "skipped"
                sched.last_run_message = "模板任务不存在或节点配置为空"
                sched.last_run_at = now
                sched.next_run_at = next_at
                sched.run_count = (sched.run_count or 0) + 1
                db.commit()
                return

            sched.last_run_at = now
            sched.last_run_task_id = new_task_id
            sched.last_run_status = "success"
            sched.last_run_message = f"已触发新任务 #{new_task_id}"
            sched.next_run_at = next_at
            sched.run_count = (sched.run_count or 0) + 1
            db.commit()

            # 异步提交真实执行
            if self._task_service_factory is not None:
                try:
                    service = self._task_service_factory()
                    asyncio.create_task(service.execute_task(new_task_id))
                except Exception as e:
                    print(f"[schedule] dispatch error: {e}")

            # 通知前端
            if self._socket_mgr is not None:
                try:
                    await self._socket_mgr.broadcast("schedule_triggered", {
                        "schedule_id": sched.id,
                        "schedule_name": sched.name,
                        "task_id": new_task_id,
                        "triggered_at": now.isoformat(),
                    })
                except Exception:
                    pass

        except Exception as e:
            sched.last_run_status = "failed"
            sched.last_run_message = f"触发失败: {e}"
            sched.last_run_at = now
            sched.next_run_at = next_at
            db.commit()
            print(f"[schedule] fire error: {e}")

    # ------------------------------------------------------------ 下次时间 ----

    def _compute_next_run(self, sched: ScheduledTask, now: datetime) -> Optional[datetime]:
        """根据触发类型计算下次执行时间"""
        if sched.trigger_type == "once":
            return None  # 一次性任务不再有下次

        if sched.trigger_type == "interval":
            minutes = sched.interval_minutes or 60
            next_at = now + timedelta(minutes=minutes)
            if sched.end_at and next_at > sched.end_at:
                return None
            return next_at

        if sched.trigger_type == "cron":
            return self._next_from_cron(sched.cron_expr, now)

        return None

    def _next_from_cron(self, expr: Optional[str], now: datetime) -> Optional[datetime]:
        """
        解析 5 字段 cron：分 时 日 月 周
        简化实现：只支持  *  N  N1,N2,N3  N1-N2  */N  形式，够覆盖绝大多数场景
        """
        if not expr:
            return None
        fields = expr.strip().split()
        if len(fields) != 5:
            return None

        minute_ok = self._cron_field(fields[0], 0, 59)
        hour_ok = self._cron_field(fields[1], 0, 23)
        day_ok = self._cron_field(fields[2], 1, 31)
        month_ok = self._cron_field(fields[3], 1, 12)
        weekday_ok = self._cron_field(fields[4], 0, 6)   # 0=周日

        # 从下一分钟开始找（最多找 2 年，避免死循环）
        candidate = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
        for _ in range(366 * 24 * 60 * 2):
            if not month_ok(candidate.month):
                # 跳到下月 1 日
                year = candidate.year + (1 if candidate.month == 12 else 0)
                month = 1 if candidate.month == 12 else candidate.month + 1
                candidate = candidate.replace(year=year, month=month, day=1, hour=0, minute=0)
                continue
            if not day_ok(candidate.day) or not weekday_ok((candidate.weekday() + 1) % 7):
                candidate = (candidate + timedelta(days=1)).replace(hour=0, minute=0)
                continue
            if not hour_ok(candidate.hour):
                candidate = (candidate + timedelta(hours=1)).replace(minute=0)
                continue
            if not minute_ok(candidate.minute):
                candidate = candidate + timedelta(minutes=1)
                continue
            return candidate
        return None

    @staticmethod
    def _cron_field(token: str, lo: int, hi: int):
        """返回一个 (int) -> bool 谓词，判断某值是否匹配 cron 字段"""
        token = token.strip()

        if token == "*":
            return lambda v: lo <= v <= hi

        values = set()
        try:
            for part in token.split(","):
                part = part.strip()
                # */N 形式
                if part.startswith("*/"):
                    step = int(part[2:])
                    for v in range(lo, hi + 1, step):
                        values.add(v)
                # N-M 范围
                elif "-" in part:
                    a, b = part.split("-", 1)
                    for v in range(int(a), int(b) + 1):
                        values.add(v)
                else:
                    values.add(int(part))
        except (ValueError, ZeroDivisionError):
            return lambda v: False
        return lambda v: v in values

    # ----------------------------------------------------------- 任务克隆 ----

    def _clone_task(self, db: Session, template_task_id: int, sched: ScheduledTask) -> Optional[int]:
        """
        从模板任务克隆一个新任务（保留同样的 test_case 和节点/分区绑定），
        并标记为 pending 等待执行。
        """
        template = db.query(Task).filter(Task.id == template_task_id).first()
        if not template:
            return None

        template_nodes = db.query(TaskNode).filter(TaskNode.task_id == template_task_id).all()
        if not template_nodes:
            return None

        new_task = Task(
            task_name=f"[{sched.name}] {template.task_name}",
            description=f"由调度 #{sched.id} 触发",
            status="pending",
            created_by=sched.created_by or template.created_by,
            test_case_id=template.test_case_id,
            is_public=template.is_public,
            start_time=datetime.utcnow(),
        )
        db.add(new_task)
        db.flush()  # 拿到 id

        for tn in template_nodes:
            db.add(TaskNode(
                task_id=new_task.id,
                node_id=tn.node_id,
                partition_id=tn.partition_id,
                status="pending",
                start_time=datetime.utcnow(),
            ))

        db.commit()
        return new_task.id


# 全局单例
schedule_service = ScheduleService()
