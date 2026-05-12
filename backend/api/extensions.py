"""
扩展 API：调度 / 基准 / 导出 / 节点健康
======================================
所有新增功能都在这个路由下，避免污染原有 api/*.py。
注册到 main.py：app.include_router(extensions.router, prefix="/api")
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_user
from models.user import User
from models.schedule import ScheduledTask
from models.baseline import PerformanceBaseline
from services.baseline_service import BaselineService
from services.export_service import ExportService
from services.node_health_service import node_health_service


router = APIRouter()


# =============================================================================
# 任务调度 API
# =============================================================================

class ScheduleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    template_task_id: int
    trigger_type: str          # once / interval / cron
    run_at: Optional[datetime] = None
    interval_minutes: Optional[int] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    cron_expr: Optional[str] = None
    enabled: bool = True


@router.post("/schedules", tags=["调度"])
def create_schedule(
    payload: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建一个定时调度"""
    # 参数校验
    if payload.trigger_type == "once" and not payload.run_at:
        raise HTTPException(400, "once 类型必须提供 run_at")
    if payload.trigger_type == "interval" and not payload.interval_minutes:
        raise HTTPException(400, "interval 类型必须提供 interval_minutes")
    if payload.trigger_type == "cron" and not payload.cron_expr:
        raise HTTPException(400, "cron 类型必须提供 cron_expr（5 字段）")

    # 计算首次 next_run_at
    next_at = payload.run_at or payload.start_at or datetime.utcnow()

    sched = ScheduledTask(
        name=payload.name,
        description=payload.description,
        template_task_id=payload.template_task_id,
        trigger_type=payload.trigger_type,
        run_at=payload.run_at,
        interval_minutes=payload.interval_minutes,
        start_at=payload.start_at,
        end_at=payload.end_at,
        cron_expr=payload.cron_expr,
        enabled=payload.enabled,
        next_run_at=next_at,
        created_by=current_user.id,
    )
    db.add(sched)
    db.commit()
    db.refresh(sched)
    return sched.to_dict()


@router.get("/schedules", tags=["调度"])
def list_schedules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    enabled_only: bool = False,
):
    q = db.query(ScheduledTask)
    # 普通用户只能看自己的；admin 可以看全部
    if current_user.role != "admin":
        q = q.filter(ScheduledTask.created_by == current_user.id)
    if enabled_only:
        q = q.filter(ScheduledTask.enabled == True)   # noqa: E712
    return [s.to_dict() for s in q.order_by(ScheduledTask.id.desc()).all()]


@router.get("/schedules/{schedule_id}", tags=["调度"])
def get_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sched = db.query(ScheduledTask).filter(ScheduledTask.id == schedule_id).first()
    if not sched:
        raise HTTPException(404, "schedule not found")
    return sched.to_dict()


@router.post("/schedules/{schedule_id}/enable", tags=["调度"])
def enable_schedule(
    schedule_id: int,
    enabled: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sched = db.query(ScheduledTask).filter(ScheduledTask.id == schedule_id).first()
    if not sched:
        raise HTTPException(404)
    sched.enabled = enabled
    db.commit()
    return {"ok": True, "enabled": sched.enabled}


@router.delete("/schedules/{schedule_id}", tags=["调度"])
def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sched = db.query(ScheduledTask).filter(ScheduledTask.id == schedule_id).first()
    if not sched:
        raise HTTPException(404)
    if current_user.role != "admin" and sched.created_by != current_user.id:
        raise HTTPException(403, "无权限删除该调度")
    db.delete(sched)
    db.commit()
    return {"ok": True}


# =============================================================================
# 性能基准 API
# =============================================================================

class BaselineCreate(BaseModel):
    name: str
    source_task_id: int
    description: Optional[str] = None
    iops_tolerance_pct: Optional[float] = 10.0
    latency_tolerance_pct: Optional[float] = 10.0
    bw_tolerance_pct: Optional[float] = 10.0
    is_active: Optional[bool] = True


@router.post("/baselines", tags=["基准"])
def create_baseline(
    payload: BaselineCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """从一个已完成的任务创建基准"""
    # 如果标记为 active，先把同 test_case 下其他基准设为 inactive
    if payload.is_active:
        from models.task import Task as _Task
        t = db.query(_Task).filter(_Task.id == payload.source_task_id).first()
        if t:
            db.query(PerformanceBaseline).filter(
                PerformanceBaseline.test_case_id == t.test_case_id,
                PerformanceBaseline.is_active == True,   # noqa: E712
            ).update({"is_active": False})
            db.commit()

    baseline = BaselineService.snapshot_from_task(
        db,
        task_id=payload.source_task_id,
        name=payload.name,
        description=payload.description,
        iops_tolerance_pct=payload.iops_tolerance_pct,
        latency_tolerance_pct=payload.latency_tolerance_pct,
        bw_tolerance_pct=payload.bw_tolerance_pct,
        is_active=payload.is_active,
        created_by=current_user.id,
    )
    if not baseline:
        raise HTTPException(400, "源任务不存在或尚未完成，无法创建基准")
    return baseline.to_dict()


@router.get("/baselines", tags=["基准"])
def list_baselines(
    test_case_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(PerformanceBaseline)
    if test_case_id is not None:
        q = q.filter(PerformanceBaseline.test_case_id == test_case_id)
    return [b.to_dict() for b in q.order_by(PerformanceBaseline.id.desc()).all()]


@router.delete("/baselines/{baseline_id}", tags=["基准"])
def delete_baseline(
    baseline_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    b = db.query(PerformanceBaseline).filter(PerformanceBaseline.id == baseline_id).first()
    if not b:
        raise HTTPException(404)
    if current_user.role != "admin" and b.created_by != current_user.id:
        raise HTTPException(403)
    db.delete(b)
    db.commit()
    return {"ok": True}


@router.get("/tasks/{task_id}/baseline-compare", tags=["基准"])
def compare_task_to_baseline(
    task_id: int,
    baseline_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """把某任务结果与指定基准（或自动选 active 基准）对比"""
    cmp = BaselineService.compare(db, task_id, baseline_id)
    if cmp is None:
        raise HTTPException(404, "task not found")
    return cmp


@router.get("/test-cases/{test_case_id}/trend", tags=["基准"])
def test_case_trend(
    test_case_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """某测试用例最近 N 次运行的趋势，含基准对比状态"""
    return BaselineService.list_compared_runs(db, test_case_id, limit=limit)


# =============================================================================
# 数据导出 API
# =============================================================================

@router.get("/tasks/{task_id}/export/metrics.csv", tags=["导出"])
def export_metrics_csv(task_id: int, db: Session = Depends(get_db)):
    data = ExportService.task_metrics_csv(db, task_id)
    return Response(
        content=data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="task_{task_id}_metrics.csv"'},
    )


@router.get("/tasks/{task_id}/export/iostat.csv", tags=["导出"])
def export_iostat_csv(task_id: int, db: Session = Depends(get_db)):
    data = ExportService.task_iostat_csv(db, task_id)
    return Response(
        content=data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="task_{task_id}_iostat.csv"'},
    )


@router.get("/tasks/{task_id}/export/report.xlsx", tags=["导出"])
def export_report_xlsx(task_id: int, db: Session = Depends(get_db)):
    data = ExportService.task_report_xlsx(db, task_id)
    if data is None:
        raise HTTPException(
            501, "服务器未安装 openpyxl，无法生成 Excel。请 `pip install openpyxl`"
        )
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="task_{task_id}_report.xlsx"'},
    )


@router.get("/tasks/export/compare.csv", tags=["导出"])
def export_compare_csv(
    task_ids: List[int] = Query(..., description="要对比的任务 ID 列表"),
    db: Session = Depends(get_db),
):
    data = ExportService.compare_tasks_csv(db, task_ids)
    return Response(
        content=data,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="tasks_compare.csv"'},
    )


# =============================================================================
# 节点健康检查 API（手动触发）
# =============================================================================

@router.post("/nodes/{node_id}/health-check", tags=["节点健康"])
async def manual_health_check(node_id: int):
    """手动触发一次节点健康检查（不等调度器轮询到）"""
    result = await node_health_service.recheck_node(node_id)
    if not result.get("ok") and result.get("message") == "node not found":
        raise HTTPException(404, "node not found")
    return result


# =============================================================================
# 审计日志 API
# =============================================================================
from models.audit import AuditLog
from services.audit_service import AuditService


@router.get("/audit-logs", tags=["审计"])
def list_audit_logs(
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    status_: Optional[str] = Query(None, alias="status"),
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """审计日志查询（按资源/用户/动作/状态过滤）"""
    # 只有管理员可以查看全部；普通用户只能看自己的
    q = db.query(AuditLog)
    if current_user.role != "admin":
        q = q.filter(AuditLog.user_id == current_user.id)

    if resource_type:
        q = q.filter(AuditLog.resource_type == resource_type)
    if resource_id:
        q = q.filter(AuditLog.resource_id == str(resource_id))
    if user_id:
        q = q.filter(AuditLog.user_id == user_id)
    if action:
        q = q.filter(AuditLog.action == action)
    if status_:
        q = q.filter(AuditLog.status == status_)

    total = q.count()
    rows = (
        q.order_by(AuditLog.created_at.desc())
        .offset(max(0, (page - 1) * page_size))
        .limit(min(500, page_size))
        .all()
    )
    return {"total": total, "page": page, "items": [r.to_dict() for r in rows]}


@router.delete("/audit-logs/cleanup", tags=["审计"])
def cleanup_audit_logs(
    days: int = 90,
    current_user: User = Depends(get_current_user),
):
    """手动清理 N 天之前的审计日志（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(403, "仅管理员可操作")
    deleted = AuditService.cleanup_older_than(days=days)
    return {"deleted": deleted, "days": days}


# =============================================================================
# 告警规则 API
# =============================================================================
from models.alert import AlertRule, AlertEvent


class AlertRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    task_id: Optional[int] = None
    test_case_id: Optional[int] = None
    metric: str
    operator: str = "gt"
    threshold: float
    consecutive_points: int = 3
    dedup_window_minutes: int = 5
    channels: List[str] = ["log"]
    webhook_url: Optional[str] = None
    email_to: Optional[str] = None
    severity: str = "warning"
    enabled: bool = True


@router.post("/alert-rules", tags=["告警"])
def create_alert_rule(
    payload: AlertRuleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.metric not in ("iops", "bandwidth", "latency", "cpu_usage", "memory_usage"):
        raise HTTPException(400, f"不支持的 metric: {payload.metric}")
    if payload.operator not in ("gt", "lt", "ge", "le"):
        raise HTTPException(400, f"不支持的 operator: {payload.operator}")

    rule = AlertRule(
        name=payload.name,
        description=payload.description,
        task_id=payload.task_id,
        test_case_id=payload.test_case_id,
        metric=payload.metric,
        operator=payload.operator,
        threshold=payload.threshold,
        consecutive_points=max(1, payload.consecutive_points),
        dedup_window_minutes=max(0, payload.dedup_window_minutes),
        channels=",".join(payload.channels) if payload.channels else "log",
        webhook_url=payload.webhook_url,
        email_to=payload.email_to,
        severity=payload.severity if payload.severity in ("info", "warning", "critical") else "warning",
        enabled=payload.enabled,
        created_by=current_user.id,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule.to_dict()


@router.get("/alert-rules", tags=["告警"])
def list_alert_rules(
    enabled_only: bool = False,
    db: Session = Depends(get_db),
):
    q = db.query(AlertRule)
    if enabled_only:
        q = q.filter(AlertRule.enabled == True)   # noqa: E712
    return [r.to_dict() for r in q.order_by(AlertRule.id.desc()).all()]


@router.post("/alert-rules/{rule_id}/enable", tags=["告警"])
def enable_alert_rule(
    rule_id: int,
    enabled: bool = True,
    db: Session = Depends(get_db),
):
    r = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not r:
        raise HTTPException(404)
    r.enabled = enabled
    db.commit()
    return {"ok": True, "enabled": r.enabled}


@router.delete("/alert-rules/{rule_id}", tags=["告警"])
def delete_alert_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not r:
        raise HTTPException(404)
    if current_user.role != "admin" and r.created_by != current_user.id:
        raise HTTPException(403)
    db.delete(r)
    db.commit()
    return {"ok": True}


@router.get("/alert-events", tags=["告警"])
def list_alert_events(
    rule_id: Optional[int] = None,
    task_id: Optional[int] = None,
    severity: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(AlertEvent)
    if rule_id:
        q = q.filter(AlertEvent.rule_id == rule_id)
    if task_id:
        q = q.filter(AlertEvent.task_id == task_id)
    if severity:
        q = q.filter(AlertEvent.severity == severity)
    total = q.count()
    rows = (
        q.order_by(AlertEvent.triggered_at.desc())
        .offset(max(0, (page - 1) * page_size))
        .limit(min(500, page_size))
        .all()
    )
    return {"total": total, "page": page, "items": [r.to_dict() for r in rows]}


# =============================================================================
# 运行批次 API（一个用例跑多次取统计值）
# =============================================================================
from fastapi import BackgroundTasks
from models.run_batch import RunBatch, RunBatchItem, RunBatchService


class RunBatchCreate(BaseModel):
    name: str
    template_task_id: int
    batch_size: int
    interval_seconds: int = 30
    description: Optional[str] = None


@router.post("/run-batches", tags=["运行批次"])
async def create_run_batch(
    payload: RunBatchCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建一个运行批次并立即开始执行（串行跑 N 次）"""
    batch = RunBatchService.create_batch(
        db,
        name=payload.name,
        template_task_id=payload.template_task_id,
        batch_size=payload.batch_size,
        interval_seconds=payload.interval_seconds,
        description=payload.description,
        created_by=current_user.id,
    )
    if not batch:
        raise HTTPException(500, "创建批次失败")

    # 后台串行执行：每个子任务跑完再跑下一个
    def _factory():
        from services.task_service import TaskService
        from core.websocket import socket_manager
        return TaskService(socket_manager)

    async def _run():
        await RunBatchService.run_batch(batch.id, _factory())

    background_tasks.add_task(_run)
    return batch.to_dict()


@router.get("/run-batches", tags=["运行批次"])
def list_run_batches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(RunBatch)
    if current_user.role != "admin":
        q = q.filter(RunBatch.created_by == current_user.id)
    return [b.to_dict(include_items=False) for b in q.order_by(RunBatch.id.desc()).all()]


@router.get("/run-batches/{batch_id}", tags=["运行批次"])
def get_run_batch(batch_id: int, db: Session = Depends(get_db)):
    b = db.query(RunBatch).filter(RunBatch.id == batch_id).first()
    if not b:
        raise HTTPException(404)
    return b.to_dict(include_items=True)


# =============================================================================
# 数据保留策略 API（手动触发一次清理）
# =============================================================================
from services.retention_service import retention_service


@router.post("/retention/run-now", tags=["数据保留"])
def run_retention_now(current_user: User = Depends(get_current_user)):
    """手动触发一次过期数据清理（仅管理员）"""
    if current_user.role != "admin":
        raise HTTPException(403, "仅管理员可操作")
    stats = retention_service.run_once()
    return {"ok": True, "stats": stats}
