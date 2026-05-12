"""
基准对比服务
============
把任务结果与基准做对比，给出：
- 各指标（IOPS/延迟/带宽）的绝对差值和百分比变化
- 自动判定 "improved / stable / regressed"
- 超出阈值的指标标红

指标判定逻辑：
- IOPS / 带宽：越高越好 —— 减少超过容忍度 ⇒ regressed
- 延迟：越低越好 —— 增加超过容忍度 ⇒ regressed
"""
from __future__ import annotations

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from models.task import Task
from models.baseline import PerformanceBaseline


class BaselineService:
    @staticmethod
    def snapshot_from_task(db: Session, task_id: int, name: str, **kwargs) -> Optional[PerformanceBaseline]:
        """
        从某个已完成的任务创建基准快照
        """
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task or task.status != "completed":
            return None

        baseline = PerformanceBaseline(
            name=name,
            description=kwargs.get("description"),
            source_task_id=task_id,
            test_case_id=task.test_case_id,
            avg_iops=float(task.avg_iops or 0),
            avg_latency_ms=float(task.avg_latency or 0),
            avg_bw_mbs=float(task.avg_bw or 0),
            iops_tolerance_pct=kwargs.get("iops_tolerance_pct", 10.0),
            latency_tolerance_pct=kwargs.get("latency_tolerance_pct", 10.0),
            bw_tolerance_pct=kwargs.get("bw_tolerance_pct", 10.0),
            is_active=kwargs.get("is_active", True),
            created_by=kwargs.get("created_by"),
        )
        db.add(baseline)
        db.commit()
        db.refresh(baseline)
        return baseline

    @staticmethod
    def compare(
        db: Session,
        task_id: int,
        baseline_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        把某任务和指定基准（或自动选择 test_case 下 is_active 基准）做对比
        """
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None

        # 选择基准
        q = db.query(PerformanceBaseline).filter(PerformanceBaseline.test_case_id == task.test_case_id)
        if baseline_id is not None:
            baseline = q.filter(PerformanceBaseline.id == baseline_id).first()
        else:
            baseline = q.filter(PerformanceBaseline.is_active == True).first()   # noqa: E712

        if not baseline:
            return {
                "task_id": task_id,
                "baseline": None,
                "message": "没有找到可用的基准（请为此测试用例先创建基准）",
            }

        def diff_metric(current: float, base: float, *, lower_is_better: bool, tolerance_pct: float):
            """计算单个指标的差异，返回 (绝对差, 百分比差, 判定)"""
            current = float(current or 0)
            base = float(base or 0)
            abs_diff = current - base
            pct = (abs_diff / base * 100) if base else 0.0

            if base == 0:
                status = "unknown"
            else:
                # 规范化：无论越高/越低好，把"变差"的方向换算成正值
                worse_pct = -pct if lower_is_better else pct
                if abs(pct) < tolerance_pct:
                    status = "stable"
                elif worse_pct > tolerance_pct:
                    status = "regressed"
                else:
                    status = "improved"
            return {
                "current": current,
                "baseline": base,
                "abs_diff": round(abs_diff, 2),
                "percent": round(pct, 2),
                "status": status,
            }

        metrics = {
            "iops": diff_metric(
                task.avg_iops, baseline.avg_iops,
                lower_is_better=False,
                tolerance_pct=float(baseline.iops_tolerance_pct),
            ),
            "latency": diff_metric(
                task.avg_latency, baseline.avg_latency_ms,
                lower_is_better=True,
                tolerance_pct=float(baseline.latency_tolerance_pct),
            ),
            "bandwidth": diff_metric(
                task.avg_bw, baseline.avg_bw_mbs,
                lower_is_better=False,
                tolerance_pct=float(baseline.bw_tolerance_pct),
            ),
        }

        # 综合判定：任一核心指标 regressed 则整体 regressed；全部 stable 则 stable；否则 improved
        statuses = [m["status"] for m in metrics.values()]
        if "regressed" in statuses:
            overall = "regressed"
        elif all(s in ("stable", "unknown") for s in statuses):
            overall = "stable"
        else:
            overall = "improved"

        return {
            "task_id": task_id,
            "task_name": task.task_name,
            "baseline": baseline.to_dict(),
            "metrics": metrics,
            "overall_status": overall,
        }

    @staticmethod
    def list_compared_runs(db: Session, test_case_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """
        列出某测试用例最近 N 次运行 + 基准对比结果
        用于前端画"趋势对比图"
        """
        rows = (
            db.query(Task)
            .filter(Task.test_case_id == test_case_id, Task.status == "completed")
            .order_by(Task.end_time.desc().nullslast())
            .limit(limit)
            .all()
        )
        result = []
        for t in reversed(rows):  # 反转成时间正序
            cmp = BaselineService.compare(db, t.id)
            result.append({
                "task_id": t.id,
                "task_name": t.task_name,
                "end_time": t.end_time.isoformat() if t.end_time else None,
                "avg_iops": float(t.avg_iops or 0),
                "avg_latency": float(t.avg_latency or 0),
                "avg_bw": float(t.avg_bw or 0),
                "comparison": cmp,
            })
        return result
