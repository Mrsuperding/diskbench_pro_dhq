# DiskBench Pro - Bug 修复清单

本次共修复了 **30+ 个 bug**，覆盖后端 FIO 执行、数据采集、DB 生命周期、SSH 连接管理，以及前端图表渲染、数据接入、内存泄漏等方面。所有修改的文件都已包含在本目录中，可直接覆盖原项目。

## 📁 修改的文件

```
backend/
├── api/
│   ├── monitor.py        ← Pydantic 兼容 / SSH 连接泄漏 / WebSocket 清理等
│   └── tasks.py          ← TaskService 构造参数修正
├── models/
│   └── case.py           ← FIO 命令生成（跨平台 + shell 注入防护）
└── services/
    ├── ssh_service.py    ← execute_command 重写 + 系统指纹探测 + 跨平台 iostat/CPU
    └── task_service.py   ← 跨平台 FIO 执行 + DB 会话修正 + 采集逻辑

frontend/src/
├── components/
│   └── PerformanceChart.vue       ← 时间轴数据规范化 / 空值防护
└── views/
    ├── monitor/
    │   ├── Index.vue              ← 移除 Math.random / 接入真实 API / 资源清理
    │   └── chart.vue              ← 修复 ref 未导入 / Y 轴单位硬编码
    └── tasks/components/
        └── TaskMetricsDialog.vue  ← 修复 nextTick 未导入 / 四张图全部更新 / 真实统计
```

---

## 🔴 一、FIO 执行相关 Bug（10 处）

| # | 问题 | 修复 |
|---|------|------|
| 1.1 | `which fio` 在 Alpine/BusyBox 等精简系统上不存在 | 改为 POSIX 标准 `command -v fio` |
| 1.2 | FIO JSON 输出被 stderr 警告污染，`json.loads` 直接崩 | 用 `--output=FILE` 参数，让 fio 把 JSON 写到独立文件 |
| 1.3 | fio 3.x 用 `lat_ns`（纳秒），fio 2.x 用 `lat`（微秒）—— 解析永远为 0 | 按版本兼容 `lat_ns / clat_ns / lat / clat` 层层兜底 |
| 1.4 | `io_engine=libaio` 在 macOS/BSD/容器中不可用 | 探测 `fio --enghelp`，按系统自动回退 `libaio → posixaio → psync` |
| 1.5 | 挂载点拼接产生 `//fio_test_file` 双斜杠 | 用 `posixpath.normpath + posixpath.join` 规范化 |
| 1.6 | FIO 超时固定 3600 秒，runtime 更长时被强制切断 | 超时动态计算 `runtime + 60s` |
| 1.7 | 挂载点不可写/不存在时直接报错 | 预先检查 `test -d && test -w`，给出清晰错误 |
| 1.8 | 测试完成后 FIO 测试文件和 JSON 输出文件不清理 | 执行完成后统一 `rm -f` 清理 |
| 1.9 | 用户输入直接拼进 shell 命令（命令注入风险） | 全部使用 `shlex.quote` 转义 |
| 1.10 | `direct=1` 在非 Linux 引擎下 fio 会警告 | 仅对 `libaio/io_uring` 才加 `--direct=1` |

## 🔴 二、SSH 执行核心 Bug（4 处，这是 FIO 长命令拿不到输出的根因）

| # | 问题 | 修复 |
|---|------|------|
| 2.1 | `channel.recv(10MB)` 只读一次就返回，命令还没完就拿到空 | 重写为**循环读取**直到 `exit_status_ready()`，结束后再把缓冲区排干 |
| 2.2 | paramiko 同步调用放在 async 函数里，阻塞事件循环 | 全部用 `loop.run_in_executor(None, ...)` 包裹 |
| 2.3 | `TCP_KEEPIDLE` 等常量在 macOS 上不存在，代码直接崩 | 用 `hasattr(socket, ...)` 保护 |
| 2.4 | 长测试 idle 断连 | 加 `transport.set_keepalive(30)` |

## 🔴 三、数据采集（iostat/CPU/内存）Bug（8 处）

| # | 问题 | 修复 |
|---|------|------|
| 3.1 | iostat 列索引硬编码 `parts[1]=tps`，但 `iostat -x` 没有 `tps` 列 | 先探测 iostat 实际输出的列名，再**按列名索引**取数 |
| 3.2 | sysstat 11/12/13 版本字段重命名（`avgqu-sz` → `aqu-sz`，`rsec/s` → `rkB/s`） | 字段名候选列表多版本兼容，单位自动换算（扇区 → KB） |
| 3.3 | iostat 第一次输出是系统启动来的累计平均值而非实时 | 加 `-y` 跳过第一次；老版本降级为采两次取最后一次 |
| 3.4 | 解析 `top` 输出在 BusyBox、procps、macOS、BSD 上格式各不相同 | Linux 改用 `/proc/stat` 两次采样差分 + `/proc/meminfo`；macOS 走 `vm_stat` |
| 3.5 | 设备前缀白名单只有 `sd/hd/nvme`，遗漏虚拟化/LVM/容器设备 | 扩充为 `sd/hd/nvme/vd/xvd/md/dm-/mmcblk/loop/rbd/dasd` |
| 3.6 | `lsblk -J`（JSON）需 util-linux 2.27+，旧系统不支持 | 探测是否支持 `-J`，不支持降级到 `df -k` 或 `df -B1` |
| 3.7 | 采集到的 CPU/内存会覆盖 FIO 结果记录（update 而非 insert） | 改为每次采集 insert 独立的 `IOPerformanceData` 点 |
| 3.8 | macOS 和 FreeBSD 的 iostat 语法完全不同 | 各自独立解析路径（macOS `iostat -d -I`、FreeBSD `iostat -x`） |

## 🔴 四、DB 会话与生命周期 Bug（3 处）

| # | 问题 | 修复 |
|---|------|------|
| 4.1 | `TaskService(db, ...)` 被后台任务调用时，请求级 db 已被 `get_db` 的 finally 关闭 | `TaskService` 不再接受 db，内部用 `SessionLocal()` 自建会话，每个协程独立 |
| 4.2 | 每个节点任务并发时共享同一个 session，存在竞态 | 每个节点协程自己 `SessionLocal()`，完成后 `db.close()` |
| 4.3 | 分区监控采集任务和主任务用同一 session 互相污染 | 监控协程也用独立 session |

## 🟡 五、SSH 连接泄漏和 API 错误处理（5 处）

| # | 问题 | 修复 |
|---|------|------|
| 5.1 | `api/monitor.py` 中每个分区都新建 SSH 连接，且失败路径不关闭 | 循环外只建一次连接，`try/finally` 确保一定关闭 |
| 5.2 | `stop_monitor` 取消任务但没等它真正退出就 close SSH | 用 `asyncio.gather(*tasks, return_exceptions=True)` 等待所有协程退出 |
| 5.3 | 接口用 `raise ValueError(...)` 抛错，FastAPI 转成 500 | 全部改为 `raise HTTPException(status_code=..., detail=...)` |
| 5.4 | `websocket` 出错后连接不清理，`list.remove` 未注册时会抛 | `disconnect` 加入存在检查；`monitor_ws` 加 `finally` 关闭 |
| 5.5 | `Pydantic.Config.orm_mode` 已在 v2 废弃 | 同时提供 `model_config = {"from_attributes": True}` 和旧版 `orm_mode`，向前兼容 |

## 🟢 六、前端渲染 Bug（10+ 处）

| # | 文件 | 问题 | 修复 |
|---|------|------|------|
| 6.1 | `chart.vue` | 用了 `ref` 但未导入，打开页面立即 `ReferenceError` 崩溃 | 加 `import { ref, computed, onMounted }` |
| 6.2 | `chart.vue` | Y 轴硬编码 `name: '%'`，IOPS/带宽/延迟也显示 % | 按 `metricKey` 自动选择单位 `%/IOPS/MB-s/ms` |
| 6.3 | `chart.vue` | `LegendComponent` 未注册 | 注册 `LegendComponent / TitleComponent` |
| 6.4 | `chart.vue` | axios 报错无任何处理 | 加 `try/catch`，记录到 `errorMsg` |
| 6.5 | `TaskMetricsDialog.vue` | 用了 `nextTick` 但未导入，对话框打开即崩溃 | 加 `nextTick` 到 import |
| 6.6 | `TaskMetricsDialog.vue` | `updateCharts` 只更新 IOPS 一张图，其他三张永远空白（`// 类似地更新...` 只有注释） | 全部四张图统一基于历史数据重绘 |
| 6.7 | `TaskMetricsDialog.vue` | `updateStatistics` 把 current 同时当作 peak/min/avg/std/p95，展示完全相等 | 改为真实聚合（max/min/avg/标准差/P95） |
| 6.8 | `TaskMetricsDialog.vue` | `updateMetricsData` 全是 `Math.random()` 假数据 | 接入 `GET /api/tasks/{id}/metrics` 真实数据 |
| 6.9 | `TaskMetricsDialog.vue` | 模板调用 `handleClose` 但未定义 | 补充定义，并在 `visible` watch 中停止轮询 |
| 6.10 | `TaskMetricsDialog.vue` | `formatBytes(0)` 会导致 `Math.log(0) = -Infinity` | 加 `<= 0` 短路 |
| 6.11 | `TaskMetricsDialog.vue` | 窗口尺寸变化时图表不自适应 | 添加 `window.resize` 监听 + `chart.resize()` |
| 6.12 | `TaskMetricsDialog.vue` | 对话框关闭后实时轮询仍在后台跑 | `watch(visible)` 自动停止 |
| 6.13 | `monitor/Index.vue` | `refreshAllData` 全是 `Math.random()` 假数据 | 接入 `/api/monitor/sample` 和 `/api/tasks/{id}/metrics` |
| 6.14 | `monitor/Index.vue` | `updateChart` 每次都重新生成 20 个随机点 | 改为维护真实历史缓存，每次刷新追加一个点 |
| 6.15 | `monitor/Index.vue` | `onMounted` 中 `nextTick` 内 async 调用与 `await nodesStore.fetchNodes()` 并发竞态 | 顺序化：先 `nextTick` → `initCharts` → `fetchNodes` → `refreshAllData` |
| 6.16 | `monitor/Index.vue` | 离开页面时 `stopMonitor` 未 catch，失败时抛错 | 加 `.catch(() => {})` |
| 6.17 | `PerformanceChart.vue` | `xAxis.type = 'time'` 要求毫秒数，但上游传的是 `toLocaleTimeString()` 本地化字符串 → ECharts 识别为 NaN，时间轴错乱 | 新增 `normalizeTs` 统一规范化时间戳 |
| 6.18 | `PerformanceChart.vue` | 数据为 null/undefined 时图表爆炸 | 新增 `safeNum`，所有数值走兜底 |

---

## 📋 一些重要的部署说明

### 后端接口约定（前端依赖这些接口返回）

前端监控页面和性能对话框都会调用：

```
GET  /api/monitor/sample                    → 返回 { ts, cpu, mem, disk }
GET  /api/monitor/history?hours=24          → 返回 [{ ts, cpu, mem, disk }, ...]
GET  /api/tasks/{task_id}/metrics?limit=N   → 返回 [{ timestamp, iops, bandwidth, latency, cpu_usage }, ...]
```

第一、二个接口在 `api/monitor.py` 中已经存在。**第三个接口**如果原后端还没实现，需要补充一个从 `IOPerformanceData` 表查数据的接口，大致如下：

```python
# 在 api/tasks.py 中添加
@router.get("/{task_id}/metrics")
async def get_task_metrics(
    task_id: int,
    limit: int = 120,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(IOPerformanceData)
        .join(TaskNode)
        .filter(TaskNode.task_id == task_id)
        .order_by(IOPerformanceData.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [r.to_dict() for r in reversed(rows)]
```

### 远程节点依赖（被测机器上需要安装的工具）

这套修复已经最大限度兼容了各系统，但节点至少需要以下工具：

| 工具 | 用途 | 在各系统的安装方式 |
|------|------|-----|
| `fio` | 磁盘压测 | `apt install fio` / `yum install fio` / `apk add fio` / `brew install fio` |
| `sysstat`（提供 iostat） | IO 性能采集 | `apt install sysstat` / `yum install sysstat` / `apk add sysstat` |
| Linux 内核 | 读 `/proc/stat`、`/proc/meminfo` | 所有 Linux 都自带 |

没有这些工具时代码会**给出明确错误提示，而不是静默失败**。
