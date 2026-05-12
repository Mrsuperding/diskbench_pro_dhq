"""
DiskBench Pro · Main Entry
==========================
本次重要改动：
1. 挂载 extensions 路由（调度 / 基准 / 导出 / 健康检查 / 审计 / 告警 / 运行批次）
2. 启动时拉起 NodeHealthService / ScheduleService / RetentionService 后台任务
3. 注入 RequestIdMiddleware + AuditMiddleware（修改类操作全自动审计）
4. 注册统一错误处理器（所有异常返回一致结构的 JSON）
5. 优雅停机：所有后台服务都能在 shutdown 时干净退出
"""
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from api import auth, nodes, cases, tasks, monitor, admin, extensions, task_node_partition
from core.config import settings
from core.database import engine, Base
from core.websocket import socket_manager
from core.errors import RequestIdMiddleware, register_exception_handlers

# 注意顺序：先 import 所有 model，再 create_all，否则 FK 引用会找不到表
from models import user, node, case, task  # noqa: F401
from models import monitor as _monitor_model  # noqa: F401
from models import schedule as _schedule_model  # noqa: F401
from models import baseline as _baseline_model  # noqa: F401
from models import audit as _audit_model  # noqa: F401
from models import alert as _alert_model  # noqa: F401
from models import run_batch as _run_batch_model  # noqa: F401
from models import task_node_partition as tnp_model  # noqa: F401

from services.node_health_service import node_health_service
from services.schedule_service import schedule_service
from services.retention_service import retention_service
from services.audit_service import AuditMiddleware


# 创建数据库表（新增 audit / alert / run_batch 等表会自动建）
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DiskBench Pro · IO 性能测试管理平台",
    description="磁盘 IO 性能测试任务下发、数据收集、数据存储与分析平台",
    version="1.2.0",
)

# ====== 中间件（顺序重要：Request-Id 要最先，审计次之）======
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuditMiddleware)          # 审计中间件（自动记录修改类操作）
app.add_middleware(RequestIdMiddleware)       # Request-Id（最先执行才能让整条链路都带 ID）

# ====== 全局异常处理 ======
register_exception_handlers(app)


if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


# ====== 路由注册 ======
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(nodes.router, prefix="/api/nodes", tags=["节点管理"])
app.include_router(cases.router, prefix="/api/cases", tags=["用例管理"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["任务管理"])
app.include_router(monitor.router, prefix="/api/monitor", tags=["监控数据"])
app.include_router(admin.router, prefix="/api/admin", tags=["系统管理"])
# 新增：扩展功能（调度 / 基准 / 导出 / 健康检查 / 审计 / 告警 / 运行批次 / 保留策略）
app.include_router(extensions.router, prefix="/api", tags=["扩展"])
# 新增：任务节点分区关联和基线管理
app.include_router(task_node_partition.router, prefix="/api", tags=["任务节点分区"])

# WebSocket
socket_manager.mount_to_app(app)


# ====== 启动/停止钩子 ======
@app.on_event("startup")
async def _on_startup():
    """
    启动所有后台服务：
    - NodeHealthService: 每 60s 检查一次节点健康
    - ScheduleService:   每 30s 扫描一次到期调度
    - RetentionService:  每 24h 清理一次过期数据
    """
    try:
        await node_health_service.start_loop(socket_manager)
    except Exception as e:
        print(f"[startup] node_health_service error: {e}")

    def _task_service_factory():
        from services.task_service import TaskService
        return TaskService(socket_manager)

    try:
        schedule_service.start(socket_manager, _task_service_factory)
    except Exception as e:
        print(f"[startup] schedule_service error: {e}")

    try:
        retention_service.start()
    except Exception as e:
        print(f"[startup] retention_service error: {e}")


@app.on_event("shutdown")
async def _on_shutdown():
    for svc, name in [
        (node_health_service, "node_health"),
        (schedule_service, "scheduler"),
        (retention_service, "retention"),
    ]:
        try:
            await svc.stop()
        except Exception as e:
            print(f"[shutdown] {name} error: {e}")


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>DiskBench Pro</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Inter,sans-serif; margin:0; padding:2rem;
                   background:linear-gradient(135deg,#1e3a8a,#3b82f6); color:#fff; min-height:100vh; }
            .wrap { max-width:1000px; margin:auto; }
            h1 { font-size:2.4rem; }
            .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
                    gap:1rem; margin-top:2rem; }
            .card { background:rgba(255,255,255,.1); padding:1rem; border-radius:8px;
                    text-decoration:none; color:#fff; border:1px solid rgba(255,255,255,.2); }
            .card:hover { background:rgba(255,255,255,.18); }
            .card h3 { margin:0 0 .4rem; }
            .card small { opacity:.75; }
        </style>
    </head>
    <body>
        <div class="wrap">
            <h1>DiskBench Pro v1.2</h1>
            <p>磁盘 IO 性能测试任务下发、数据收集、数据存储与分析平台</p>
            <div class="grid">
                <a class="card" href="/docs"><h3>API 文档</h3><small>Swagger UI</small></a>
                <a class="card" href="/api/schedules"><h3>定时调度</h3><small>自动化压测</small></a>
                <a class="card" href="/api/baselines"><h3>性能基准</h3><small>回归检测</small></a>
                <a class="card" href="/api/alert-rules"><h3>告警规则</h3><small>阈值触发</small></a>
                <a class="card" href="/api/run-batches"><h3>运行批次</h3><small>多次取稳定值</small></a>
                <a class="card" href="/api/audit-logs"><h3>审计日志</h3><small>操作追溯</small></a>
                <a class="card" href="/health"><h3>健康状态</h3><small>存活检查</small></a>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.2.0",
        "services": {
            "node_health": node_health_service._task is not None,
            "scheduler": schedule_service._task is not None,
            "retention": retention_service._task is not None,
        },
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
