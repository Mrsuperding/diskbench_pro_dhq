# 数据库连接池问题排查文档

## 问题描述

任务界面刷新时出现间歇性失败，错误信息：

```
sqlalchemy.exc.InterfaceError: (pymysql.err.InterfaceError) (0, '')
```

错误发生在 `get_db` 依赖注入的 `db.close()` 阶段。

---

## 问题定位

### 1. 表面现象

- 只有任务界面会间歇性刷新失败
- 其他界面（节点、用例）正常
- 并发请求时更容易触发

### 2. 根本原因：StaticPool 单连接

**`backend/core/database.py` 原始配置：**

```python
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=StaticPool,  # 问题根源
    ...
)
```

**`StaticPool` 的特点：**
- 只有 **1 个连接**
- 所有请求共享这个连接
- 连接被占用时，其他请求等待

当任务列表页有多个并发请求时：
- 请求 A 获取连接
- 请求 B 等待
- 请求 C 等待
- ...
- 超时或连接池耗尽

### 3. 加重因素：N+1 查询

**原始 `get_tasks` 实现（200+ 次查询/请求）：**

```python
@router.get("/", response_model=List[TaskListResponse])
async def get_tasks(...):
    tasks = query.offset(skip).limit(limit).all()  # 1次查询

    for task in tasks:  # N 次循环
        node_count = db.query(TaskNode).filter(  # 每次循环 1 次 count 查询
            TaskNode.task_id == task.id
        ).count()

        task.test_case.case_name  # 每次循环 1 次 lazy loading
```

假设 100 个任务 = **1 + 100 + 100 = 201 次数据库查询**

查询时间长 = 连接持有时间长 = 并发能力更低

---

## 解决方案

### 1. 连接池配置优化

**修改 `backend/core/database.py`：**

```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,           # 基础连接数
    max_overflow=20,        # 允许超额的最大连接数
    pool_timeout=30,        # 获取连接超时时间（秒）
    pool_recycle=1800,      # 30分钟回收连接
    pool_pre_ping=True,     # 使用前检查连接有效性
    echo=False
)
```

**参数说明：**

| 参数 | 值 | 说明 |
|------|-----|------|
| `pool_size` | 10 | 基础连接数 |
| `max_overflow` | 20 | 允许超额的最大连接数（峰值可达 10+20=30） |
| `pool_timeout` | 30 | 获取连接超时时间（秒） |
| `pool_recycle` | 1800 | 30分钟回收连接，避免 MySQL `wait_timeout` 超时 |
| `pool_pre_ping` | True | 使用前检查连接有效性，无效连接自动重建 |

### 2. N+1 查询优化

**修改 `backend/api/tasks.py`：**

```python
from sqlalchemy.orm import joinedload
from sqlalchemy import func

@router.get("/", response_model=List[TaskListResponse])
async def get_tasks(...):
    # 1. 使用 joinedload 预加载 test_case（避免 lazy loading）
    query = db.query(Task).options(joinedload(Task.test_case))

    tasks = query.offset(skip).limit(limit).all()

    # 2. 一次性获取所有任务的节点数量（子查询）
    task_ids = [t.id for t in tasks]
    node_counts = {}
    if task_ids:
        counts = db.query(
            TaskNode.task_id,
            func.count(TaskNode.id).label('count')
        ).filter(
            TaskNode.task_id.in_(task_ids)
        ).group_by(TaskNode.task_id).all()
        node_counts = {tc.task_id: tc.count for tc in counts}

    # 3. 构建结果
    for task in tasks:
        task_data = {
            **task.to_dict(),
            "test_case_name": task.test_case.case_name,  # 预加载，无额外查询
            "node_count": node_counts.get(task.id, 0)   # 已有计数，无额外查询
        }
        result.append(task_data)
```

**优化效果：**

| 场景 | 优化前 | 优化后 |
|------|--------|--------|
| 100 个任务 | 201 次查询 | 3 次查询 |
| 查询类型 | N+1 | 子查询 + JOIN |

---

## 验证方法

### 1. 导入验证

```bash
cd D:\delvelop_project\ai_project\diskbench_pro\backend
python -c "from main import app; print('OK')"
```

### 2. 并发测试

```bash
# 终端1：启动后端
python start_backend.py

# 终端2：并发请求测试
for i in {1..20}; do
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/tasks/ &
done
wait
```

### 3. 观察连接数

```sql
-- MySQL 中查看当前连接数
SHOW PROCESSLIST;
```

正常情况下，连接数应该 <= `pool_size + max_overflow` (30)

---

## 相关文件

| 文件 | 修改内容 |
|------|----------|
| `backend/core/database.py` | StaticPool → QueuePool |
| `backend/api/tasks.py` | N+1 查询优化为子查询 + joinedload |

---

## 经验总结

1. **永远不要在生产环境使用 `StaticPool`** - 只适合单连接/测试场景

2. **警惕 N+1 查询** - ORM 的 lazy loading 在循环中会触发大量查询

3. **使用 `joinedload` 预加载关联对象** - 将 N+1 转为 JOIN 查询

4. **使用子查询批量获取计数** - 比循环中 count() 高效得多

5. **`pool_pre_ping=True` 很重要** - 自动检测无效连接，避免 MySQL 超时后的连接失效
