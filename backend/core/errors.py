"""
统一错误处理
============
目标：
1. 所有异常返回结构一致的 JSON：{code, message, detail, request_id}
2. HTTPException 按原状态码返回；其他未捕获异常统一返回 500
3. 给每个请求打一个 request_id，方便在日志中串联
4. 校验错误（Pydantic）给出更友好的中文提示
"""
from __future__ import annotations

import traceback
import uuid
from typing import Any

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import IntegrityError, OperationalError


class RequestIdMiddleware(BaseHTTPMiddleware):
    """给每个请求分配一个 UUID，写入 request.state 并回显到响应头"""

    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-Id") or uuid.uuid4().hex[:12]
        request.state.request_id = rid
        response = await call_next(request)
        response.headers["X-Request-Id"] = rid
        return response


def _error_body(code: int, message: str, detail: Any = None, request_id: str = None):
    return {
        "code": code,
        "message": message,
        "detail": detail,
        "request_id": request_id,
    }


def register_exception_handlers(app: FastAPI):
    """注册全局异常处理器"""

    @app.exception_handler(HTTPException)
    async def _http_exc(request: Request, exc: HTTPException):
        rid = getattr(request.state, "request_id", None)
        # 保留原 status_code，body 结构统一
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(
                code=exc.status_code,
                message=str(exc.detail) if exc.detail else "请求出错",
                detail=None,
                request_id=rid,
            ),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_exc(request: Request, exc: RequestValidationError):
        rid = getattr(request.state, "request_id", None)
        # 把 Pydantic 的错误转换成更容易看的结构
        pretty = []
        for err in exc.errors():
            pretty.append({
                "field": ".".join(str(p) for p in err.get("loc", [])),
                "type": err.get("type"),
                "message": err.get("msg"),
            })
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body(
                code=422,
                message="请求参数校验失败",
                detail=pretty,
                request_id=rid,
            ),
        )

    @app.exception_handler(IntegrityError)
    async def _integrity_exc(request: Request, exc: IntegrityError):
        rid = getattr(request.state, "request_id", None)
        # 常见的唯一约束/外键冲突
        raw = str(exc.orig) if exc.orig else str(exc)
        if "UNIQUE" in raw or "Duplicate" in raw or "unique" in raw:
            msg = "资源已存在或唯一字段冲突"
        elif "foreign key" in raw.lower():
            msg = "关联资源不存在或被引用中"
        else:
            msg = "数据一致性错误"
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=_error_body(
                code=409,
                message=msg,
                detail=raw[:300],
                request_id=rid,
            ),
        )

    @app.exception_handler(OperationalError)
    async def _db_op_exc(request: Request, exc: OperationalError):
        rid = getattr(request.state, "request_id", None)
        print(f"[error] DB OperationalError [{rid}]:\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=_error_body(
                code=503,
                message="数据库暂时不可用，请稍后再试",
                detail=str(exc.orig)[:300] if exc.orig else str(exc)[:300],
                request_id=rid,
            ),
        )

    @app.exception_handler(Exception)
    async def _fallback_exc(request: Request, exc: Exception):
        rid = getattr(request.state, "request_id", None)
        # 服务端错误一定要打全 stack，方便排障
        print(f"[error] Unhandled exception [{rid}]:\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body(
                code=500,
                message="服务器内部错误",
                detail=str(exc)[:300],
                request_id=rid,
            ),
        )
