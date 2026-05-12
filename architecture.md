# IO性能测试管理平台 - 系统架构

## 技术栈更新

### 后端技术栈
- **框架**: FastAPI (Python)
- **数据库**: MySQL 8.0
- **ORM**: SQLAlchemy
- **认证**: JWT (PyJWT)
- **密码哈希**: bcrypt
- **WebSocket**: fastapi-socketio
- **任务队列**: Celery + Redis
- **API文档**: FastAPI自动生成的Swagger/OpenAPI

### 前端技术栈
- **框架**: 原生JavaScript (ES6+)
- **样式**: Tailwind CSS
- **图表**: ECharts.js
- **实时通信**: Socket.IO
- **HTTP客户端**: Axios
- **构建工具**: Vite

## 系统架构设计

### 1. 后端架构 (FastAPI)
```
app/
├── api/                    # API路由
│   ├── auth.py            # 认证接口
│   ├── nodes.py           # 节点管理
│   ├── cases.py           # 用例管理
│   ├── tasks.py           # 任务管理
│   ├── monitor.py         # 监控数据
│   └── admin.py           # 管理员接口
├── core/                   # 核心组件
│   ├── config.py          # 配置管理
│   ├── security.py        # 安全工具
│   ├── database.py        # 数据库连接
│   └── websocket.py       # WebSocket管理
├── models/                 # 数据模型
│   ├── user.py            # 用户模型
│   ├── node.py            # 节点模型
│   ├── case.py            # 用例模型
│   └── task.py            # 任务模型
├── schemas/                # Pydantic模式
├── services/               # 业务逻辑
│   ├── ssh_service.py     # SSH连接服务
│   ├── fio_service.py     # FIO执行服务
│   └── monitor_service.py # 监控服务
└── main.py                 # 应用入口
```

### 2. 前端架构
```
frontend/
├── src/
│   ├── api/               # API接口
│   ├── components/        # 可复用组件
│   ├── pages/            # 页面组件
│   ├── utils/            # 工具函数
│   ├── assets/           # 静态资源
│   └── main.js           # 入口文件
├── public/               # 公共资源
└── index.html            # HTML模板
```

## 核心功能模块设计

### 1. 认证与授权模块
- JWT令牌认证
- 角色基础访问控制 (RBAC)
- 用户权限验证中间件
- 管理员权限提升

### 2. 节点管理模块
- SSH连接管理
- 节点状态检测
- 分区信息收集
- 节点配置CRUD

### 3. 用例管理模块
- FIO参数模板
- 参数验证与约束
- 用例版本控制
- 模板复用机制

### 4. 任务调度模块
- 异步任务执行
- 任务状态管理
- 进度实时推送
- 错误处理机制

### 5. 监控数据模块
- 实时数据采集
- IO性能分析
- 图表数据聚合
- 历史数据存储

## API设计规范

### RESTful API结构
```
# 认证相关
POST /api/auth/login          # 用户登录
POST /api/auth/logout         # 用户登出
GET  /api/auth/me             # 获取当前用户信息

# 节点管理
GET    /api/nodes             # 获取节点列表
POST   /api/nodes             # 创建节点
GET    /api/nodes/{id}        # 获取节点详情
PUT    /api/nodes/{id}        # 更新节点
DELETE /api/nodes/{id}        # 删除节点
GET    /api/nodes/{id}/status # 获取节点状态

# 用例管理
GET    /api/cases             # 获取用例列表
POST   /api/cases             # 创建用例
GET    /api/cases/{id}        # 获取用例详情
PUT    /api/cases/{id}        # 更新用例
DELETE /api/cases/{id}        # 删除用例

# 任务管理
GET    /api/tasks             # 获取任务列表
POST   /api/tasks             # 创建任务
GET    /api/tasks/{id}        # 获取任务详情
PUT    /api/tasks/{id}        # 更新任务
DELETE /api/tasks/{id}        # 删除任务
POST   /api/tasks/{id}/start  # 启动任务
POST   /api/tasks/{id}/stop   # 停止任务
POST   /api/tasks/{id}/clone  # 克隆任务

# 监控数据
GET    /api/monitor/{task_id}/performance # 获取性能数据
GET    /api/monitor/{task_id}/iostat      # 获取iostat数据
GET    /api/monitor/{task_id}/logs        # 获取任务日志

# WebSocket事件
/ws/monitor/{task_id}         # 实时监控数据推送
```

## 数据库交互设计

### SQLAlchemy模型关系
- 用户 -> 节点 (一对多)
- 用户 -> 用例 (一对多)
- 用户 -> 任务 (一对多)
- 任务 -> 测试用例 (多对一)
- 任务 -> 节点 (多对多，通过中间表)
- 节点 -> 分区 (一对多)

### 性能优化策略
- 数据库连接池
- 查询优化与索引
- 缓存机制 (Redis)
- 分页与懒加载

## 安全设计

### 1. 认证安全
- JWT令牌过期机制
- 刷新令牌策略
- 密码复杂度要求
- 登录失败锁定

### 2. 数据传输安全
- HTTPS加密传输
- 敏感数据加密存储
- SQL注入防护
- XSS攻击防护

### 3. 权限安全
- 基于角色的访问控制
- 资源级权限验证
- 操作审计日志
- 管理员操作限制

## 部署架构

### 1. 开发环境
- FastAPI开发服务器
- MySQL本地实例
- Redis本地实例
- 前端开发服务器

### 2. 生产环境
- Gunicorn + Uvicorn工作进程
- MySQL主从复制
- Redis集群
- Nginx反向代理
- Docker容器化部署