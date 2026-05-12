"""
告警引擎
========
核心流程：
  评估新采集到的数据 → 匹配规则 → 满足条件且超出去重窗口 → 记录事件 + 通知

集成方式：
  在 task_service._parse_fio_results 或 _monitor_node_performance 采集到新性能点后调用：
    await AlertEngine.evaluate(db, task_id, task_node_id, metric_point)
  metric_point: {'iops': ..., 'bandwidth': ..., 'latency': ..., 'cpu_usage': ...}

通知通道：
- log:     print 到控制台 + 写入 task_logs
- webhook: POST 一个 JSON 到 rule.webhook_url
- email:   预留接口，具体 SMTP 配置由 core/config.py 提供（此处先占位）
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List

import httpx
from sqlalchemy.orm import Session

from core.database import SessionLocal
from models.alert import AlertRule, AlertEvent
from models.task import Task, TaskLog


class AlertEngine:
    # 每个 task_node 维护"连续满足条件的计数器"以支持 consecutive_points
    # key: (rule_id, task_node_id)  value: int
    _streak_counter: Dict[tuple, int] = {}

    @staticmethod
    async def evaluate(
        db: Session,
        task_id: int,
        task_node_id: Optional[int],
        metric_point: Dict[str, float],
    ):
        """
        给定一个采样点，评估所有匹配的规则。
        该方法不抛异常；告警失败只记录日志。
        """
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return

            # 筛出可能匹配的规则
            rules = (
                db.query(AlertRule)
                .filter(AlertRule.enabled == True)   # noqa: E712
                .filter(
                    (AlertRule.task_id == task_id)
                    | (AlertRule.task_id.is_(None) & AlertRule.test_case_id == task.test_case_id)
                    | (AlertRule.task_id.is_(None) & AlertRule.test_case_id.is_(None))
                )
                .all()
            )

            for rule in rules:
                observed = metric_point.get(rule.metric)
                if observed is None:
                    continue
                observed = float(observed)
                threshold = float(rule.threshold)

                if AlertEngine._match(observed, rule.operator, threshold):
                    key = (rule.id, task_node_id or 0)
                    AlertEngine._streak_counter[key] = AlertEngine._streak_counter.get(key, 0) + 1

                    if AlertEngine._streak_counter[key] < (rule.consecutive_points or 1):
                        continue  # 还没连续满足足够次数

                    # 检查去重窗口
                    if AlertEngine._within_dedup(db, rule, task_id):
                        continue

                    # 触发告警
                    await AlertEngine._trigger(db, rule, task_id, task_node_id, observed)
                    AlertEngine._streak_counter[key] = 0  # 重置计数器
                else:
                    # 不匹配 → 重置连续计数
                    AlertEngine._streak_counter.pop((rule.id, task_node_id or 0), None)
        except Exception as e:
            print(f"[alert] evaluate error: {e}")

    # ------------------------------------------------------------------ 内部 ----

    @staticmethod
    def _match(observed: float, op: str, threshold: float) -> bool:
        if op == "gt":
            return observed > threshold
        if op == "ge":
            return observed >= threshold
        if op == "lt":
            return observed < threshold
        if op == "le":
            return observed <= threshold
        return False

    @staticmethod
    def _within_dedup(db: Session, rule: AlertRule, task_id: int) -> bool:
        """判断同规则 + 同 task 最近是否已经触发过"""
        window = rule.dedup_window_minutes or 0
        if window <= 0:
            return False
        since = datetime.utcnow() - timedelta(minutes=window)
        cnt = (
            db.query(AlertEvent)
            .filter(AlertEvent.rule_id == rule.id)
            .filter(AlertEvent.task_id == task_id)
            .filter(AlertEvent.triggered_at >= since)
            .count()
        )
        return cnt > 0

    @staticmethod
    async def _trigger(
        db: Session,
        rule: AlertRule,
        task_id: int,
        task_node_id: Optional[int],
        observed: float,
    ):
        """记录一个 AlertEvent 并发送通知"""
        message = (
            f"[{rule.severity.upper()}] {rule.name}: "
            f"{rule.metric} = {observed:.2f} "
            f"（规则 {rule.operator} {float(rule.threshold):.2f}）"
        )
        event = AlertEvent(
            rule_id=rule.id,
            task_id=task_id,
            task_node_id=task_node_id,
            metric=rule.metric,
            observed_value=observed,
            threshold=rule.threshold,
            severity=rule.severity,
            message=message,
        )
        db.add(event)
        db.flush()

        # 写入 task_logs 便于在任务详情页看到
        db.add(TaskLog(
            task_id=task_id,
            log_level="warning" if rule.severity != "info" else "info",
            message=message,
            source="alert",
        ))
        db.commit()
        db.refresh(event)

        # 异步发送通知，不阻塞采集
        asyncio.create_task(AlertEngine._notify(rule, event))

    @staticmethod
    async def _notify(rule: AlertRule, event: AlertEvent):
        channels = [c.strip() for c in (rule.channels or "log").split(",") if c.strip()]
        err: Optional[str] = None
        try:
            for ch in channels:
                if ch == "log":
                    print(f"[ALERT] {event.message}")
                elif ch == "webhook":
                    await AlertEngine._send_webhook(rule, event)
                elif ch == "email":
                    await AlertEngine._send_email(rule, event)
        except Exception as e:
            err = str(e)[:500]
        finally:
            # 更新通知结果
            db = SessionLocal()
            try:
                e = db.query(AlertEvent).filter(AlertEvent.id == event.id).first()
                if e:
                    e.notification_sent = err is None
                    e.notification_error = err
                    db.commit()
            except Exception:
                pass
            finally:
                db.close()

    @staticmethod
    async def _send_webhook(rule: AlertRule, event: AlertEvent):
        if not rule.webhook_url:
            raise ValueError("rule.webhook_url not configured")
        payload = {
            "event_id": event.id,
            "rule_id": rule.id,
            "rule_name": rule.name,
            "severity": event.severity,
            "metric": event.metric,
            "observed_value": float(event.observed_value),
            "threshold": float(event.threshold),
            "task_id": event.task_id,
            "task_node_id": event.task_node_id,
            "message": event.message,
            "triggered_at": event.triggered_at.isoformat() if event.triggered_at else None,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(rule.webhook_url, json=payload)
            r.raise_for_status()

    @staticmethod
    async def _send_email(rule: AlertRule, event: AlertEvent):
        """邮件通知占位，SMTP 配置需在 core/config.py 补充"""
        # TODO: 实际发送邮件需要 smtplib + SMTP 配置
        # 这里只打印，方便先跑通
        print(f"[email stub] send to {rule.email_to}: {event.message}")
