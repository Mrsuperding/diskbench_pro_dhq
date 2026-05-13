# CHANGELOG - 2026-05-13

## 概述

本次更新包含以下主要改进：
1. 任务节点分区支持多分区合并显示
2. 修复任务执行时分区数据为空导致的错误
3. 节点管理增强（编辑功能、工具目录支持）
4. Docker 部署支持
5. 克隆任务时复制分区信息

---

## 1. 数据模型变更

### backend/models/task.py

**TaskNode 模型新增 `partitions` 字段**：
```python
# 支持多个分区：逗号分隔的分区路径
partitions = Column(Text, nullable=True)
```

**TaskNode.to_dict() 更新**：
```python
"partitions": self.partitions or "",
```

### backend/models/node.py

**Node 模型新增 `tool_path` 字段**：
```python
tool_path = Column(String(500), nullable=True, comment="工具目录路径")
```

### database-schema.sql

```sql
ALTER TABLE task_nodes ADD COLUMN partitions TEXT NULL;
ALTER TABLE task_nodes MODIFY COLUMN partition_id INT NULL;
```

---

## 2. API 变更

### backend/api/tasks.py

#### get_task 预加载优化
```python
task = db.query(Task).options(
    joinedload(Task.test_case),
    selectinload(Task.task_nodes).joinedload(TaskNode.node),
    selectinload(Task.task_nodes).joinedload(TaskNode.partition)
).filter(Task.id == task_id).first()
```

#### add_task_node 合并逻辑
同一个节点添加多次时，合并分区到同一个 TaskNode：
```python
existing = db.query(TaskNode).filter(
    TaskNode.task_id == task_id,
    TaskNode.node_id == task_node_data.node_id
).first()
if existing:
    existing.partitions = ','.join(partition_paths)
    # ... 更新状态等
else:
    db_task_node = TaskNode(
        task_id=task_id,
        node_id=task_node_data.node_id,
        partition_id=placeholder_partition.id,
        partitions=','.join(partition_paths)
    )
```

#### clone_task 克隆分区信息
```python
cloned_task_node = TaskNode(
    task_id=cloned_task.id,
    node_id=task_node.node_id,
    partition_id=task_node.partition_id,
    partitions=task_node.partitions  # 新增：克隆分区信息
)
```

#### 新增 update_task_node 接口
用于从任务详情页编辑节点分区。

### backend/api/nodes.py

#### 新增工具上传接口
```
POST /{node_id}/upload-tools
```
接收 multipart/form-data，上传工具文件到节点的 tool_path。

### backend/schemas/task.py

#### TaskNodeUpdate 新增字段
```python
partition_path: Optional[str] = None  # 逗号分隔的分区路径
```

#### TaskNodeUpdate 导入修复
确保 `TaskNodeUpdate` 在主 import 中可用。

---

## 3. 服务层变更

### backend/services/ssh_service.py

#### SFTP 文件操作
```python
def upload_file(self, local_path, remote_path): ...
def upload_dir(self, local_path, remote_path): ...
def ensure_dir_exists(self, path): ...
def file_exists(self, path): ...
```

#### libaio 检测修复
检测逻辑移出 `if not fio_found:` 块，确保始终执行。

#### 工具路径获取
```python
def get_tool_path(self, tool_name, tool_path=None):
    """获取工具路径，优先使用 tool_path"""
    if tool_path:
        tool_full_path = posixpath.join(tool_path, tool_name)
        if self.file_exists(tool_full_path):
            return tool_full_path
    # 回退到系统默认
    return f"command -v {tool_name}"
```

### backend/services/task_service.py

#### 挂载点检查逻辑修复
```python
# 优先使用 task_node.partitions（逗号分隔），否则回退到 partition.mount_point
mount_point_to_check = partition_paths[0] if partition_paths else (partition.mount_point if partition else None)
```

#### FIO 执行时工具目录支持
```python
fio_path = await ssh_service.get_tool_path("fio", ssh_service.tool_path)
```

---

## 4. 前端变更

### frontend/src/views/tasks/Detail.vue

#### 节点列表显示分区
```vue
<span>{{ row.partitions || row.partition?.mount_point || `分区 ${row.partition_id}` }}</span>
```

#### 点击节点名称编辑分区
```javascript
const handleEditNodePartitions = (taskNode) => {
  editNodeForm.value = {
    task_node_id: taskNode.id,
    node_id: taskNode.node_id,
    node_name: taskNode.node?.name || `节点 ${taskNode.node_id}`,
    partitions: taskNode.partitions || taskNode.partition?.mount_point || ''
  }
  editNodePartitionsVisible.value = true
}
```

#### 添加节点时发送所有分区
```javascript
const handleAddNode = async () => {
  // 不再循环调用，改为一次性发送所有分区
  partition_path: nodeForm.value.partitions || ''
}
```

### frontend/src/views/nodes/Index.vue

- 点击节点名称打开编辑对话框
- 移除独立的"详情"按钮，改为下拉菜单中的"查看详情"
- 显示 tool_path 字段

### frontend/src/router/index.js

- 移除 `/nodes/:id` 路由

### frontend/src/api/tasks.js

- 新增 `updateTaskNodePartitions` API 方法

---

## 5. Docker 部署

### 新增文件
- `backend/Dockerfile`
- `frontend/Dockerfile`
- `frontend/nginx.conf`
- `docker-compose.yml`
- `DEPLOYMENT.md`

---

## 6. 错误修复

| 问题 | 解决方案 |
|------|---------|
| 409 Conflict on add node | 前端改为一次性发送所有分区 |
| partition_id cannot be null | 修改列为 nullable |
| 422 missing task_node_update | TaskNodeUpdate 加入主 import |
| AttributeError partition.mount_point | 使用 mount_point_to_check 变量 |
| 分区信息为空 | get_task 预加载 task_nodes 及其关联 |
| 克隆任务分区为空 | clone_task 时复制 partitions 字段 |

---

## 7. 数据库迁移命令

```sql
-- 添加 partitions 字段
ALTER TABLE task_nodes ADD COLUMN partitions TEXT NULL;

-- 允许 partition_id 为空
ALTER TABLE task_nodes MODIFY COLUMN partition_id INT NULL;
```
