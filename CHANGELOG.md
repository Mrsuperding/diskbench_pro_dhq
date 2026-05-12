# DiskBench Pro · 变更总览

本版本基于原项目在以下方面做了系统性改进，全部改动都已合并到源码里。

## 📚 详细文档

| 文档 | 说明 |
|------|------|
| `BUG_FIX_REPORT.md`      | 30+ 个 bug 的修复清单（FIO 跨系统、SSH 执行、iostat 解析、DB 会话等） |
| `NEW_FEATURES.md`        | 新增的 10 项能力：调度/基准/告警/审计/运行批次/数据导出/健康检查/保留策略/加密/错误处理 |
| `TIME_WINDOW_FEATURE.md` | 性能抖动图的时间窗格滑动查看功能 |
| `UI_REDESIGN.md`         | UI 简化：浅色工作台风格、原子组件、旧类名兼容层 |

## 🚀 快速启动

### 后端
```bash
cd backend
pip install -r requirements.txt

# 生产环境必做：设置加密密钥
export DISKBENCH_SECRET_KEY="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"

python main.py
```

### 前端
```bash
cd frontend
npm install
npm run dev
```

## 📦 新增的 API 速览

```
# 调度
POST/GET/DELETE /api/schedules          /api/schedules/{id}/enable

# 基准
POST/GET/DELETE /api/baselines
GET /api/tasks/{id}/baseline-compare
GET /api/test-cases/{id}/trend

# 导出
GET /api/tasks/{id}/export/metrics.csv
GET /api/tasks/{id}/export/iostat.csv
GET /api/tasks/{id}/export/report.xlsx
GET /api/tasks/export/compare.csv?task_ids=1&task_ids=2

# 节点健康
POST /api/nodes/{id}/health-check

# 审计
GET/DELETE /api/audit-logs

# 告警
POST/GET/DELETE /api/alert-rules           /api/alert-rules/{id}/enable
GET /api/alert-events

# 运行批次
POST/GET /api/run-batches                   GET /api/run-batches/{id}

# 数据保留
POST /api/retention/run-now
```

## 📋 后端新增的 Python 包

在 `backend/requirements.txt` 中已经追加：
- `paramiko>=3.3`（原来漏了）
- `psutil>=5.9`（原来漏了）
- `openpyxl>=3.1.2`（导出 Excel 用）
- `cryptography>=41`（加密凭据用）

## 🎨 前端新增页面

- `/schedules`    定时调度
- `/baselines`    性能基准
- `/alerts`       告警
- `/run-batches`  运行批次
- `/audit-logs`   审计日志

路由已在 `frontend/src/router/index.js` 中注册完毕。

## ⚠️ 需要你手动确认的一点

前端监控页（TaskMetricsDialog 和 monitor/Index.vue）会调用：
```
GET /api/tasks/{id}/metrics?limit=600
```
这个接口在原后端 `api/tasks.py` 中**可能尚未实现**。如果前端抖动图拉不到数据，按下面示例在 `api/tasks.py` 里补一个即可：

```python
from models.task import IOPerformanceData, TaskNode

@router.get("/{task_id}/metrics")
async def get_task_metrics(
    task_id: int,
    limit: int = 120,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(IOPerformanceData)
        .join(TaskNode, IOPerformanceData.task_node_id == TaskNode.id)
        .filter(TaskNode.task_id == task_id)
        .order_by(IOPerformanceData.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [r.to_dict() for r in reversed(rows)]
```

## 🗃️ 数据库

- 启动时 `Base.metadata.create_all(...)` 会自动创建新增的表：
  - `scheduled_tasks`、`performance_baselines`、`audit_logs`、`alert_rules`、`alert_events`、`run_batches`、`run_batch_items`
- 节点的 `password`/`private_key` 字段已改为加密存储
  - **已有的明文数据兼容**（没有 `ENC:v1:` 前缀的会按明文对待）
  - 建议运行一次迁移脚本把旧数据也加密：`UPDATE nodes SET password = password` 会触发 ORM 重新加密（或写个简单 Python 脚本遍历 nodes 重存）
