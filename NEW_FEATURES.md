# DiskBench Pro · 新增能力清单（v1.2）

本次在"bug 修复版 (v1.1)"的基础上，补齐了**专业磁盘性能测试平台**应有的核心能力。

## ✨ 新增能力一览

| 类别 | 能力 | 文件 | API |
|------|------|------|-----|
| 🔒 **安全** | 节点凭据加密存储 | `core/crypto.py` + `models/node.py` | 透明，无需调用 |
| 🔒 **安全** | 请求审计日志 | `models/audit.py` + `services/audit_service.py` | `/api/audit-logs` |
| 🔒 **安全** | 统一错误处理 | `core/errors.py` | 所有 API 自动生效 |
| ⚙️ **自动化** | 定时任务调度 | `models/schedule.py` + `services/schedule_service.py` | `/api/schedules` |
| ⚙️ **自动化** | 节点健康检查 | `services/node_health_service.py` | `/api/nodes/{id}/health-check` |
| ⚙️ **自动化** | 数据保留策略 | `services/retention_service.py` | `/api/retention/run-now` |
| 📊 **分析** | 性能基准对比 | `models/baseline.py` + `services/baseline_service.py` | `/api/baselines` |
| 📊 **分析** | 多运行批次 | `models/run_batch.py` | `/api/run-batches` |
| 📊 **分析** | 数据导出 (CSV/Excel) | `services/export_service.py` | `/api/tasks/{id}/export/*` |
| 🔔 **监控** | 阈值告警引擎 | `models/alert.py` + `services/alert_engine.py` | `/api/alert-rules` + `/api/alert-events` |

## 🎯 P0 核心能力详解

### 1. 节点凭据加密存储

**问题**：原项目把节点 SSH 密码和私钥**明文**存在数据库，一旦数据库泄漏后果严重。

**解决**：
- 新增 `core/crypto.py`，用 Fernet（AES-128 + HMAC-SHA256）对称加密
- 密钥来源优先级：环境变量 `DISKBENCH_SECRET_KEY` > `~/.diskbench/secret.key` 文件 > 自动生成
- 使用 SQLAlchemy `TypeDecorator` 自动加解密，**业务代码完全透明**
- **向前兼容**：历史明文数据（没有 `ENC:v1:` 前缀）自动按明文对待，不会报错
- 默认 `to_dict()` 不返回凭据，避免 API 误泄漏
- 新增 `has_password` / `has_private_key` 字段提示前端是否已配置

**生产部署**：
```bash
# 生成密钥
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# 写入环境变量
export DISKBENCH_SECRET_KEY="生成的密钥"
```

### 2. 请求审计日志

**能力**：
- 所有 `POST/PUT/PATCH/DELETE` 请求自动入库（GET 不记录，避免写爆）
- 记录：**谁、何时、对什么资源、做了什么、来源 IP、结果状态**
- 从 URL 智能提取 `resource_type` 和 `resource_id`
- 失败操作也记录（含异常信息）
- 审计写入用**独立 session**，不会影响业务事务；写失败只打日志，不抛异常

**过滤与检索**：
```
GET /api/audit-logs?resource_type=task&resource_id=123
GET /api/audit-logs?user_id=5&action=start
GET /api/audit-logs?status=failure
```

### 3. 节点健康检查

**能力**：
- 后台每 **60 秒**并发（并发度 10）SSH 探活所有节点
- 连续失败 **3 次**才标 offline（防网络抖动误杀）
- 状态变化自动通过 WebSocket 广播给前端
- 提供手动触发接口：`POST /api/nodes/{id}/health-check`
- 记录 `last_health_check_at` / `last_online_at` / `health_fail_count` / `health_message`

### 4. 定时任务调度

**三种触发方式**：
- `once`：指定时间执行一次
- `interval`：每 N 分钟执行一次（可设 `start_at` / `end_at`）
- `cron`：5 字段 cron 表达式（内置解析器，支持 `* N N1,N2 N1-N2 */N`）

**关键设计**：
- 每次触发**克隆**一个新的 Task 实例运行，历史按次独立保留（方便做趋势分析）
- 每 30 秒扫描一次到期调度，持久化 `next_run_at` 字段，重启不丢
- 触发失败会记录到 `last_run_status` + `last_run_message`，前端可看
- 支持启用/禁用 (`POST /api/schedules/{id}/enable?enabled=true`)

**典型场景**：
```json
// 每天凌晨 2 点跑一次基准压测
{
  "name": "夜间基准",
  "template_task_id": 42,
  "trigger_type": "cron",
  "cron_expr": "0 2 * * *"
}
```

### 5. 性能基准对比

**能力**：
- 选择某次已完成任务，一键保存为"性能基准"
- 后续任务自动对比基准，给出 IOPS / 延迟 / 带宽的**绝对差**、**百分比差**、**状态判定**
- 状态判定考虑"越高越好"（IOPS/带宽）还是"越低越好"（延迟）
- 可配置每个指标的**容忍度**（默认 10%）：波动在容忍度内 = stable，超过视为 improved/regressed
- 综合判定：任一指标 regressed 则整体 regressed

**API**：
```
POST   /api/baselines                              创建基准
GET    /api/tasks/{id}/baseline-compare            单次任务对比
GET    /api/test-cases/{id}/trend?limit=20         用例最近 N 次趋势
```

### 6. 数据导出

**三种导出**：
| 端点 | 格式 | 内容 |
|------|------|------|
| `/tasks/{id}/export/metrics.csv` | CSV | 性能采样（含 BOM，Excel 直接打开不乱码） |
| `/tasks/{id}/export/iostat.csv`  | CSV | iostat 采样 |
| `/tasks/{id}/export/report.xlsx` | XLSX | 4 个 sheet：Summary / Nodes / Metrics（含 IOPS 趋势图） / IOStat |
| `/tasks/export/compare.csv?task_ids=1&task_ids=2...` | CSV | 多任务横向对比 |

## 🎯 P1 增强能力详解

### 7. 多运行批次

**解决什么问题**：单次压测结果抖动大，需要跑 N 次取统计值才可信。

**设计**：
- 创建一个 RunBatch，指定 `batch_size`（如 5 次）和 `interval_seconds`（两次之间间隔）
- 后台**串行**跑 N 次（必须串行，防止互相干扰）
- 全部完成后自动算 **avg / median / stdev / P95 / CV（变异系数）**
- **CV = stdev/avg × 100** 能很好地反映性能稳定性：CV < 5% 算稳定，> 15% 说明抖动严重

### 8. 告警引擎

**规则配置**：
- 监控范围：全部任务 / 指定任务 / 指定测试用例
- 指标：`iops` / `bandwidth` / `latency` / `cpu_usage` / `memory_usage`
- 比较：`gt` / `lt` / `ge` / `le`
- 防毛刺：`consecutive_points=3` 意味着连续 3 个采样点都命中条件才触发
- 防告警风暴：`dedup_window_minutes=5` 意味着同规则同任务 5 分钟内不重复告警
- 严重程度：`info` / `warning` / `critical`

**通知通道**：
- `log`：控制台 + task_logs
- `webhook`：POST 一个 JSON 到 `webhook_url`（可接入企业微信、钉钉、Slack）
- `email`：预留，SMTP 需自行补配置

**集成**：
在 `task_service._parse_fio_results` 采集到新数据后调用：
```python
from services.alert_engine import AlertEngine
await AlertEngine.evaluate(db, task_id, task_node_id, {
    'iops': total_iops,
    'bandwidth': total_bw_mbs,
    'latency': avg_latency_ms,
})
```

### 9. 数据保留策略

**能力**：
- 每 24 小时后台自动清理过期数据
- 保留天数可通过环境变量调节：
  - `RETENTION_METRICS_DAYS`（默认 30）—— 性能/iostat 采样
  - `RETENTION_TASK_LOGS_DAYS`（默认 60）—— 任务日志
  - `RETENTION_AUDIT_DAYS`（默认 90）—— 审计日志
  - `RETENTION_ALERTS_DAYS`（默认 90）—— 告警事件
- **受基准引用的任务数据永不清理**（否则基准对比会失效）
- 提供手动触发接口：`POST /api/retention/run-now`（需要管理员权限）

### 10. 统一错误处理

**能力**：
- 所有 API 异常返回结构一致的 JSON：
  ```json
  {
    "code": 404,
    "message": "task not found",
    "detail": null,
    "request_id": "a1b2c3d4e5f6"
  }
  ```
- 每个请求分配唯一 `X-Request-Id`，响应头回显，日志打印可串联
- 专门处理：
  - `HTTPException`：按原状态码
  - `RequestValidationError`：友好的字段级错误提示
  - `IntegrityError`：唯一冲突 / 外键冲突自动识别
  - `OperationalError`：数据库连接问题返回 503
  - 其他未捕获异常：500 + 完整 stack trace 到后端日志

## 📦 所有新增文件（16 个）

```
backend/
├── core/
│   ├── crypto.py               ← NEW: 凭据加密
│   └── errors.py               ← NEW: 统一错误处理
├── models/
│   ├── node.py                 ← UPDATED: 加密字段 + 健康字段
│   ├── schedule.py             ← NEW: 调度
│   ├── baseline.py             ← NEW: 性能基准
│   ├── audit.py                ← NEW: 审计
│   ├── alert.py                ← NEW: 告警规则 + 事件
│   └── run_batch.py            ← NEW: 运行批次
├── services/
│   ├── node_health_service.py  ← NEW
│   ├── schedule_service.py     ← NEW
│   ├── baseline_service.py     ← NEW
│   ├── export_service.py       ← NEW
│   ├── audit_service.py        ← NEW
│   ├── alert_engine.py         ← NEW
│   └── retention_service.py    ← NEW
├── api/
│   └── extensions.py           ← NEW: 所有新 API
├── main.py                     ← UPDATED
└── requirements.txt            ← UPDATED
```

## 🔌 集成步骤

1. **覆盖文件**：把 `diskbench_fixes/backend/` 覆盖到原项目 `backend/`
2. **安装新依赖**：
   ```bash
   pip install -r backend/requirements.txt
   ```
3. **设置加密密钥**（生产环境必做）：
   ```bash
   export DISKBENCH_SECRET_KEY="<Fernet key>"
   ```
4. **启动**：
   ```bash
   python backend/main.py
   ```
   启动日志会显示后台服务已拉起：
   ```
   [health] ...
   [schedule] ...
   [retention] ...
   ```
5. **数据库自动建表**：首次启动会自动创建 `scheduled_tasks` / `performance_baselines` / `audit_logs` / `alert_rules` / `alert_events` / `run_batches` / `run_batch_items` 等新表

## 🎁 告警集成示例

要让告警引擎真正生效，需要在 `task_service.py` 采集到新数据时调用它。推荐在 `_parse_fio_results` 尾部添加：

```python
from services.alert_engine import AlertEngine

# 在 db.commit() 之后
await AlertEngine.evaluate(db, task_id, task_node_id, {
    'iops': total_iops,
    'bandwidth': total_bw_mbs,
    'latency': avg_lat_ms,
    'cpu_usage': 0,  # 若此处能拿到系统数据可填入
    'memory_usage': 0,
})
```

## 📝 API 一览（新增）

```
# 调度
POST   /api/schedules
GET    /api/schedules
GET    /api/schedules/{id}
POST   /api/schedules/{id}/enable
DELETE /api/schedules/{id}

# 基准
POST   /api/baselines
GET    /api/baselines
DELETE /api/baselines/{id}
GET    /api/tasks/{id}/baseline-compare
GET    /api/test-cases/{id}/trend

# 导出
GET    /api/tasks/{id}/export/metrics.csv
GET    /api/tasks/{id}/export/iostat.csv
GET    /api/tasks/{id}/export/report.xlsx
GET    /api/tasks/export/compare.csv?task_ids=1&task_ids=2

# 节点健康
POST   /api/nodes/{id}/health-check

# 审计日志
GET    /api/audit-logs
DELETE /api/audit-logs/cleanup

# 告警
POST   /api/alert-rules
GET    /api/alert-rules
POST   /api/alert-rules/{id}/enable
DELETE /api/alert-rules/{id}
GET    /api/alert-events

# 运行批次
POST   /api/run-batches
GET    /api/run-batches
GET    /api/run-batches/{id}

# 数据保留
POST   /api/retention/run-now
```

## 🚧 后续可继续增强（P2）

- **前端 UI**：目前只做了后端 API，需要为每个新能力做对应页面（调度管理 / 基准管理 / 告警规则 / 运行批次 / 审计日志查看器）
- **FIO 高级参数**：fadvise、numa 绑核、多 job、独立 iodepth
- **任务模板市场**：预置常用压测模板（4K 随机读、128K 顺序写、混合负载等）
- **集群对比**：同一个用例在多个节点上的横向对比
- **Prometheus 指标导出**：暴露 `/metrics` 端点供 Prometheus 抓取
- **邮件告警通道**：补完 SMTP 发送逻辑
