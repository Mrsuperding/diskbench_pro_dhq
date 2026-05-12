"""
审计日志服务
============
提供两种记录方式：
1. 显式调用 AuditService.log(...)：适合关键操作（删除/修改节点、启动任务）
2. 中间件自动记录：所有非 GET/OPTIONS 请求都自动入库

写入设计：
- 用独立的 SessionLocal，避免阻塞业务事务
- 失败时只打日志，不抛异常（审计失败不能影响业务）
- 提供批量清理接口（留给数据保留策略用）
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sqlalchemy.orm import Session

from core.database import SessionLocal
from models.audit import AuditLog


# 不记录审计的路径（高频 / 无敏感信息）
_SKIP_PATHS = {
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/",
}
# 不记录审计的路径前缀
_SKIP_PREFIXES = (
    "/static/",
    "/api/monitor/sample",     # 高频轮询
    "/api/monitor/ws",         # WebSocket 路径
    "/socket.io/",
)


class AuditService:
    @staticmethod
    def log(
        action: str,
        *,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: str = "success",
        message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
    ) -> Optional[AuditLog]:
        """显式记录一条审计日志"""
        db = SessionLocal()
        try:
            entry = AuditLog(
                user_id=user_id,
                username=username,
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id is not None else None,
                status=status,
                message=(message[:2000] if message else None),
                ip_address=ip_address,
                user_agent=(user_agent[:500] if user_agent else None),
                request_method=request_method,
                request_path=request_path,
            )
            db.add(entry)
            db.commit()
            db.refresh(entry)
            return entry
        except Exception as e:
            # 审计失败不应影响业务
            print(f"[audit] log error: {e}")
            try:
                db.rollback()
            except Exception:
                pass
            return None
        finally:
            db.close()

    @staticmethod
    def cleanup_older_than(days: int = 90) -> int:
        """清理超过 N 天的审计日志，返回清理条数"""
        if days <= 0:
            return 0
        db = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            count = (
                db.query(AuditLog)
                .filter(AuditLog.created_at < cutoff)
                .delete(synchronize_session=False)
            )
            db.commit()
            return count
        except Exception as e:
            db.rollback()
            print(f"[audit] cleanup error: {e}")
            return 0
        finally:
            db.close()


class AuditMiddleware(BaseHTTPMiddleware):
    """
    自动审计中间件。
    只记录 POST / PUT / PATCH / DELETE 请求（修改类操作），
    避免 GET/监控轮询写爆审计表。
    """

    AUDIT_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if request.method not in self.AUDIT_METHODS:
            return await call_next(request)
        if path in _SKIP_PATHS:
            return await call_next(request)
        if any(path.startswith(p) for p in _SKIP_PREFIXES):
            return await call_next(request)

        # 提前记录请求元数据（即使 call_next 抛异常也要审计）
        ip = request.client.host if request.client else None
        ua = request.headers.get("user-agent")
        user_id = None
        username = None

        response: Optional[Response] = None
        status_code = 500
        err_msg: Optional[str] = None
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            err_msg = str(e)[:500]
            raise
        finally:
            # 解析用户（如果路由通过 get_current_user 写入了 request.state.user 可取用）
            user = getattr(request.state, "user", None)
            if user is not None:
                user_id = getattr(user, "id", None)
                username = getattr(user, "username", None)

            AuditService.log(
                action=self._infer_action(request.method, path),
                user_id=user_id,
                username=username,
                resource_type=self._infer_resource(path),
                resource_id=self._infer_resource_id(path),
                status="success" if 200 <= status_code < 400 else "failure",
                message=(err_msg if err_msg else f"HTTP {status_code}"),
                ip_address=ip,
                user_agent=ua,
                request_method=request.method,
                request_path=path,
            )

        return response

    # ---------- 从路径推断动作/资源 ----------
    @staticmethod
    def _infer_action(method: str, path: str) -> str:
        low = path.lower()
        if "/login" in low:
            return "login"
        if "/logout" in low:
            return "logout"
        if "/start" in low:
            return "start"
        if "/stop" in low:
            return "stop"
        if "/health-check" in low:
            return "health_check"
        if "/export/" in low:
            return "export"
        return method.lower()

    @staticmethod
    def _infer_resource(path: str) -> Optional[str]:
        # /api/{resource}/{id}/...
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 2 and parts[0] == "api":
            # 把复数名还原成单数
            raw = parts[1]
            return raw.rstrip("s").replace("-", "_") or raw
        return None

    @staticmethod
    def _infer_resource_id(path: str) -> Optional[str]:
        parts = [p for p in path.split("/") if p]
        # /api/tasks/123 /api/tasks/123/start
        for i, p in enumerate(parts):
            if p.isdigit():
                return p
        return None
