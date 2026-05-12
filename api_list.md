# diskbench_pro 后端API接口列表

## 项目概述
diskbench_pro是一个IO性能性能测试管理平台，采用前后前后端分离架构，基于FastAPI + MySQL + JavaScript技术栈开发。

## 基础信息
- **API基础路径**: `/api`
- **认证方式**: JWT Token认证
- **数据格式**: JSON

## 接口分类

### 1. 认证相关接口

#### 1.1 用户注册
- **URL**: `/api/auth/register`
- **方法**: `POST`
- **描述**: 用户注册
- **请求体**: 
  ```json
  {
    "username": "string",
    "email": "string",
    "password": "string"
  }
  ```
- **响应**: 用户信息

#### 1.2 用户登录
- **URL**: `/api/auth/login`
- **方法**: `POST`
- **描述**: 用户登录
- **请求体**: 
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **响应**: Token信息和用户信息

#### 1.3 刷新令牌
- **URL**: `/api/auth/refresh`
- **方法**: `POST`
- **描述**: 刷新访问令牌
- **请求体**: 
  ```json
  {
    "refresh_token": "string"
  }
  ```
- **响应**: 新的访问令牌

#### 1.4 获取当前用户信息
- **URL**: `/api/auth/me`
- **方法**: `GET`
- **描述**: 获取当前用户信息
- **请求头**: `Authorization: Bearer {token}`
- **响应**: 当前用户信息

#### 1.5 更新当前用户信息
- **URL**: `/api/auth/me`
- **方法**: `PUT`
- **描述**: 更新当前用户信息
- **请求头**: `Authorization: Bearer {token}`
- **请求体**: 
  ```json
  {
    "email": "string",
    "avatar": "string"
  }
  ```
- **响应**: 更新后的用户信息

#### 1.6 修改密码
- **URL**: `/api/auth/change-password`
- **方法**: `POST`
- **描述**: 修改密码
- **请求头**: `Authorization: Bearer {token}`
- **请求体**: 
  ```json
  {
    "old_password": "string",
    "new_password": "string"
  }
  ```
- **响应**: 操作结果

#### 1.7 用户登出
- **URL**: `/api/auth/logout`
- **方法**: `POST`
- **描述**: 用户登出
- **请求头**: `Authorization: Bearer {token}`
- **响应**: 操作结果

#### 1.8 获取用户列表（管理员）
- **URL**: `/api/auth/users`
- **方法**: `GET`
- **描述**: 获取用户列表（仅管理员）
- **请求头**: `Authorization: Bearer {token}`
- **响应**: 用户列表

#### 1.9 更新用户角色（管理员）
- **URL**: `/api/auth/users/{user_id}/role`
- **方法**: `PUT`
- **描述**: 更新用户角色（仅管理员）
- **请求头**: `Authorization: Bearer {token}`
- **请求体**: 
  ```json
  {
    "role": "admin|user"
  }
  ```
- **响应**: 操作结果

#### 1.10 更新用户状态（管理员）
- **URL**: `/api/auth/users/{user_id}/status`
- **方法**: `PUT`
- **描述**: 更新用户状态（仅管理员）
- **请求头**: `Authorization: Bearer {token}`
- **请求体**: 
  ```json
  {
    "is_active": true|false
  }
  ```
- **响应**: 操作结果

### 2. 节点管理接口

#### 2.1 获取节点列表
- **URL**: `/api/nodes/`
- **方法**: `GET`
- **描述**: 获取节点列表
- **请求头**: `Authorization: Bearer {token}`
- **参数**: 
  - `skip`: 跳过数量
  - `limit`: 限制数量
  - `status_filter`: 状态筛选
- **响应**: 节点列表

#### 2.2 获取节点详情
- **URL**: `/api/nodes/{node_id}`
- **方法**: `GET`
- **描述**: 获取节点节点详情
- **请求头**: `Authorization: Bearer {token}`
- **响应**: 节点详情

#### 2.3 创建节点
- **URL**: `/api/nodes/`
- **方法**: `POST`
- **描述**: 创建节点
- **请求头**: `Authorization: Bearer {token}`
- **请求体**: 
  ```json
  {
    "node_name": "string",
    "host": "string",
    "port": "integer",
    "login_type": "string",
    "username": "string",
    "password": "string",
    "private_key": "string",
    "os_type": "string",
    "is_public": true|false
  }
  ```
- **响应**: 创建的节点信息

#### 2.4 更新节点
- **URL**: `/api/nodes/{node_id}`
- **方法**: `PUT`
- **描述**: 更新节点
- **请求头**: `Authorization: Bearer {token}`
- **请求体**: 节点信息（部分字段）
- **响应**: 更新后的节点信息

#### 2.5 删除节点
- **URL**: `/api/nodes/{node_id}`
- **方法**: `DELETE`
- **描述**: 删除节点
- **请求头**: `Authorization: Bearer {token}`
- **响应**: 操作结果

#### 2.6 测试节点连接
- **URL**: `/api/nodes/{node_id}/test-connection`
- **方法**: `POST`
- **描述**: 测试节点连接
- **请求头**: `Authorization: Bearer {token}`
- **响应**: 连接结果和系统信息

#### 2.7 测试连接（不保存节点）
- **URL**: `/api/nodes/test-connection`
- **方法**: `POST`
- **描述**: 测试连接（不保存节点）
- **请求头**: `Authorization: Bearer {token}`
- **请求体**: 连接信息
- **响应**: 连接结果和系统信息

#### 2.8 更新节点状态
- **URL**: `/api/nodes/{node_id}/status`
- **方法**: `PUT`
- **描述**: 更新节点状态
- **请求头**: `Authorization: Bearer {token}`
- **请求体**: 
  ```json
  {
    "status": "string"
  }
  ```
- **响应**: 操作结果

#### 2.9 获取节点分区列表
- **URL**: `/api/nodes/{node_id}/partitions`
- **方法**: `GET`
- **描述**: 获取节点分区列表
- **请求头**: `Authorization: Bearer {token}`
- **响应**: 分区列表

#### 2.10 创建节点分区
- **URL**: `/api/nodes/{node_id}/partitions`
- **方法**: `POST`
- **描述**: 创建节点分区
- **请求头**: `Authorization: Bearer {token}`
- **请求体**: 分区信息
- **响应**: 创建的分区信息

#### 2.11 更新节点分区
- **URL**: `/api/nodes/{node_id}/partitions/{partition_id}`
- **方法**: `PUT`
- **描述**: 更新节点分区
- **请求头**: `Authorization: Bearer {token}`
- **请求体**: 分区信息（部分字段）
- **响应**: 更新后的分区信息

#### 2.12 删除节点分区
- **URL**: `/api/nodes/{node_id}/partitions/{partition_id}`
- **方法**: `DELETE`
- **描述**: 删除节点分区
- **请求头**: `Authorization: Bearer {token}`
- **响应**: 操作结果

### 3. 用例管理接口

#### 3.1 获取测试用例列表
- **URL**: `/api/cases/`
- **方法**: `GET`
- **描述**: 获取测试用例列表
- **请求头**: `Authorization: Bearer {token}`
- **参数**: 
  - `skip`: 跳过数量
  - `limit`: 限制数量
  - `template_only`: 是否只显示模板
- **响应**: 测试用例列表

#### 3.2 获取测试用例详情
- **URL**: `/api/cases/{case_id}`
- **方法**: `GET`
- **描述**: 获取测试用例详情
- **请求头**: `Authorization: Bearer {token}`
- **响应**: 测试用例详情

#### 3.3 创建测试用例
- **URL**: `/api/cases/`
- **方法**: `POST`
- **描述**: 创建测试用例
- **请求头**: `Authorization: Bearer {token}`
- **请求体**: 测试用例信息
- **响应**: 创建的测试用例信息

#### 3.4 更新测试用例
- **URL**: `/api/cases/{case_id}`
- **方法**: `PUT`
- **描述**: 更新测试用例
- **请求头**: `Authorization: Bearer {token}`
- **请求体**: 测试用例信息（部分字段）
- **响应**: 更新后的测试用例信息

#### 3.5 删除测试用例
- **URL**: `/api/cases/{case_id}`
- **方法**: `DELETE`
- **描述**: 删除测试用例
- **请求头**: `Authorization: Bearer {token}`
- **响应**: 操作结果

#### 3.6 获取FIO命令
- **URL**: `/api/cases/{case_id}/fio-command`
- **方法**: `GET`
- **描述**: 获取FIO命令
- **请求头**: `Authorization: Bearer {token}`
- **参数**: 
  - `filename`: 测试文件名
- **响应**: FIO命令信息

#### 3.7 克隆测试用例
- **URL**: `/api/cases/{case_id}/clone`
- **方法**: `POST`
- **描述**: 克隆测试用例
- **请求头**: `Authorization: Bearer {token}`
- **请求体**: 
  ```json
  {
    "new_name": "string"
  }
  ```
- **响应**: 克隆的测试用例信息

#### 3.8 获取用例模板
- **URL**: `/api/cases/templates/`
- **方法**: `GET`
- **描述**: 获取用例模板
- **请求头**: `Authorization: Bearer {token}`
- **响应**: 用例模板列表

#### 3.9 设置用例为模板
- **URL**: `/api/cases/{case_id}/set-template`
- **方法**: `POST`
- **描述**: 设置用例为模板
- **请求头**: `Authorization: Bearer {token}`
- **请求体**: 
  ```json
  {
    "is_template": true|false
  }
  ```
- **响应**: 操作结果

#### 3.10 搜索测试用例
- **URL**: `/api/cases/search/`
- **方法**: `GET`
- **描述**: 搜索测试用例
- **请求头**: `Authorization: Bearer {token}`
- **参数**: 
  - `query`: 搜索关键词
  - `limit`: 限制数量
- **响应**: 搜索结果

### 4. 任务管理接口

#### 4.1 获取任务列表
- **URL**: `/api/tasks/`
- **方法**: `GET`
- **描述**: 获取任务列表
- **请求头**: `Authorization: Bearer {token}`
- **参数**: 
  - `skip`: 跳过数量
  - `limit`: 限制数量
  - `status_filter`: 状态筛选
- **响应**: 任务列表

#### 4.2 获取任务详情
- **URL**: `/api/tasks/{task_id}`
- **方法**: `GET`
- **描述**: 获取任务详情
- **请求头**: `Authorization: Bearer {token}`
- **响应**: 任务详情

#### 4.3 创建任务
- **URL**: `/api/tasks/`
- **方法**: `POST`
- **描述**: 创建任务
- **请求头**: `Authorization: Bearer {token}`
- **请求体**: 任务信息
- **响应**: 创建的任务信息

#### 4.4 更新任务
- **URL**: `/api/tasks/{task_id}`
- **方法**: `PUT`
- **描述**: 更新任务
- **请求头**: `Authorization: Bearer {token}`
- **请求体**: 任务信息（部分字段）
- **响应**: 更新后的任务信息

#### 4.5 删除任务
- **URL**: `/api/tasks/{task_id}`
- **方法**: `DELETE`
- **描述**: 删除任务
- **请求头**: `Authorization: Bearer {token}`
- **响应**: 操作结果

#### 4.6 启动任务
- **URL**: `/api/tasks/{task_id}/start`
- **方法**: `POST`
- **描述**: 启动任务
- **请求头**: `Authorization: Bearer {token}`
- **响应**: 操作结果

### 5. 监控接口

#### 5.1 瞬时采样
- **URL**: `/api/monitor/sample`
- **方法**: `GET`
- **描述**: 获取系统瞬时采样数据
- **请求头**: `Authorization: Bearer {token}`
- **响应**: 系统采样数据

#### 5.2 WebSocket监控
- **URL**: `/api/monitor/ws`
- **方法**: `WebSocket`
- **描述**: WebSocket实时监控
- **请求头**: `Authorization: Bearer {token}`
- **响应**: 实时监控数据

#### 5.3 获取历史监控数据
- **URL**: `/api/monitor/history`
- **方法**: `GET`
- **描述**: 获取历史监控数据
- **请求头**: `Authorization: Bearer {token}`
- **参数**: 
  - `hours`: 小时数
- **响应**: 历史监控数据

### 6. 管理员接口

#### 6.1 获取用户列表
- **URL**: `/api/admin/users`
- **方法**: `GET`
- **描述**: 获取用户列表（仅管理员）
- **请求头**: `Authorization: Bearer {token}`
- **响应**: 用户列表

#### 6.2 切换超级用户
- **URL**: `/api/admin/user/{user_id}/toggle`
- **方法**: `POST`
- **描述**: 切换超级用户状态（仅管理员）
- **请求头**: `Authorization: Bearer {token}`
- **响应**: 操作结果

#### 6.3 热重载配置文件
- **URL**: `/api/admin/reload_config`
- **方法**: `POST`
- **描述**: 热重载配置文件（仅管理员）
- **请求头**: `Authorization: Bearer {token}`
- **响应**: 操作结果

## 权限说明
- **普通用户**: 只能访问和操作自己创建的资源
- **管理员**: 可以访问和操作所有资源

## 错误码说明
- **400**: 请求参数错误
- **401**: 未认证或认证失败
- **403**: 权限不足
- **404**: 资源不存在
- **500**: 服务器内部错误

## 备注
- 所有需要认证的接口都需要在请求头中添加 `Authorization: Bearer {token}`
- 接口返回格式统一为JSON
- 具体的请求参数和响应格式可以参考对应的模型定义
