# IO性能测试管理平台

一个专业的前后端分离IO性能测试管理系统，基于FastAPI + MySQL + JavaScript技术栈开发。

## 功能特性

### 🖥️ 核心功能
- **节点管理**: 分布式测试节点管理，支持SSH连接和分区信息同步
- **用例管理**: FIO测试用例配置，支持多种IO模式和参数设置
- **任务管理**: 创建和执行IO测试任务，实时监控任务进度和性能数据
- **权限控制**: 基于角色的访问控制，支持任务可见性设置
- **实时监控**: WebSocket实时数据推送，IO抖动图表展示
- **日志管理**: 完整的任务执行日志和iostat监控数据

### 🎨 技术特色
- **现代化UI**: 响应式设计，支持桌面端和移动端
- **实时通信**: WebSocket实时数据推送
- **数据可视化**: ECharts图表展示性能数据
- **动画效果**: Anime.js流畅的交互动画
- **专业设计**: 工业级界面风格，科技感十足

## 技术架构

### 后端技术栈
- **框架**: FastAPI (Python)
- **数据库**: MySQL 8.0
- **ORM**: SQLAlchemy
- **认证**: JWT (PyJWT)
- **密码哈希**: bcrypt
- **WebSocket**: python-socketio
- **任务队列**: 异步任务执行

### 前端技术栈
- **框架**: 原生JavaScript (ES6+)
- **样式**: Tailwind CSS
- **图表**: ECharts.js
- **实时通信**: Socket.IO
- **动画**: Anime.js

## 快速开始

### 环境要求
- Python 3.8+
- MySQL 8.0+
- Node.js 16+ (可选，用于前端开发服务器)

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd io-performance-platform
   ```

2. **安装后端依赖**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **配置数据库**
   ```bash
   # 创建数据库
   mysql -u root -p
   CREATE DATABASE io_test_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

4. **配置环境变量**
   ```bash
   # 创建.env文件
   cp .env.example .env
   # 编辑.env文件，设置数据库连接等信息
   ```

5. **启动后端服务**
   ```bash
   cd backend
   python main.py
   ```

6. **访问系统**
   - 前端界面: http://localhost:8000
   - API文档: http://localhost:8000/docs
   - 管理员账号: admin / admin123
   - 普通用户: demo / demo123

### 前端开发

```bash
# 启动前端开发服务器
cd frontend
npm install
npm run dev
```

## 项目结构

```
io-performance-platform/
├── backend/                    # 后端API服务
│   ├── api/                   # API路由
│   ├── core/                  # 核心组件
│   ├── models/                # 数据模型
│   ├── schemas/               # 数据验证模式
│   ├── services/              # 业务逻辑服务
│   ├── main.py               # 应用入口
│   └── requirements.txt      # Python依赖
├── frontend/                  # 前端界面
│   ├── src/                  # 源代码
│   │   ├── js/              # JavaScript文件
│   │   ├── resources/       # 静态资源
│   │   └── index.html       # 主页面
│   └── public/              # 公共资源
├── database-schema.sql       # 数据库结构
├── architecture.md          # 系统架构文档
├── interaction.md           # 交互设计文档
├── design.md               # 视觉设计指南
└── README.md              # 项目说明
```

## 核心模块

### 1. 认证与权限管理
- JWT令牌认证
- 角色基础访问控制 (RBAC)
- 用户权限验证中间件

### 2. 节点管理模块
- SSH连接管理
- 节点状态检测和同步
- 分区信息收集
- 批量节点操作

### 3. 用例管理模块
- FIO参数模板配置
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

## API接口

### 认证相关
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/register` - 用户注册
- `GET /api/auth/me` - 获取当前用户信息

### 节点管理
- `GET /api/nodes/` - 获取节点列表
- `POST /api/nodes/` - 创建节点
- `GET /api/nodes/{id}` - 获取节点详情
- `PUT /api/nodes/{id}` - 更新节点
- `DELETE /api/nodes/{id}` - 删除节点

### 用例管理
- `GET /api/cases/` - 获取用例列表
- `POST /api/cases/` - 创建用例
- `GET /api/cases/{id}` - 获取用例详情
- `PUT /api/cases/{id}` - 更新用例

### 任务管理
- `GET /api/tasks/` - 获取任务列表
- `POST /api/tasks/` - 创建任务
- `GET /api/tasks/{id}` - 获取任务详情
- `POST /api/tasks/{id}/start` - 启动任务
- `POST /api/tasks/{id}/stop` - 停止任务

## 配置说明

### 数据库配置
```sql
-- 创建数据库
CREATE DATABASE io_test_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 导入表结构
source database-schema.sql
```

### 环境变量配置 (.env)
```
# 数据库配置
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/io_test_platform

# 安全配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis配置
REDIS_URL=redis://localhost:6379

# CORS配置
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

## 使用说明

### 创建第一个测试

1. **添加节点**
   - 进入"节点管理"页面
   - 点击"添加节点"
   - 填写节点信息（主机地址、用户名、认证方式）
   - 测试连接并保存

2. **创建用例**
   - 进入"用例管理"页面
   - 点击"创建用例"
   - 配置FIO参数（读写模式、块大小、队列深度等）
   - 保存用例

3. **执行任务**
   - 进入"任务管理"页面
   - 点击"创建任务"
   - 选择测试用例和目标节点
   - 启动任务并实时监控

### 查看测试结果

- **实时图表**: 任务执行过程中的IO性能图表
- **执行日志**: 详细的任务执行日志和错误信息
- **性能报告**: 任务完成后的性能统计报告
- **历史数据**: 历史任务的性能数据对比

## 高级功能

### 任务克隆
支持一键克隆现有任务配置，快速创建相似测试任务。

### 模板管理
将常用用例保存为模板，方便快速创建新用例。

### 权限共享
支持设置任务和节点的可见性，实现团队协作。

### 实时监控
WebSocket实时推送性能数据，支持IO抖动分析。

## 故障排查

### 常见问题

1. **数据库连接失败**
   - 检查MySQL服务是否启动
   - 确认数据库用户权限
   - 检查连接字符串配置

2. **SSH连接失败**
   - 确认目标节点SSH服务正常
   - 检查防火墙设置
   - 验证用户名和密码/密钥

3. **FIO执行失败**
   - 确认目标节点已安装FIO
   - 检查磁盘挂载权限
   - 验证测试路径是否存在

### 日志查看

```bash
# 后端日志
tail -f backend/logs/app.log

# 数据库日志
tail -f /var/log/mysql/mysql.log
```

## 开发指南

### 后端开发
- 使用FastAPI框架，遵循RESTful API设计
- 数据库操作使用SQLAlchemy ORM
- 异步处理使用async/await语法
- WebSocket实时通信使用python-socketio

### 前端开发
- 使用原生JavaScript，遵循ES6+标准
- 样式框架使用Tailwind CSS
- 图表使用ECharts.js
- 实时通信使用Socket.IO

### 代码规范
- 遵循PEP 8 Python编码规范
- 使用类型提示增强代码可读性
- 添加充分的注释和文档字符串
- 保持函数和类的单一职责原则

## 部署说明

### 生产环境部署

1. **服务器准备**
   - 安装Python 3.8+
   - 安装MySQL 8.0+
   - 配置防火墙和安全组

2. **应用部署**
   - 使用Gunicorn作为WSGI服务器
   - 配置Nginx反向代理
   - 设置进程守护（supervisor/systemd）

3. **数据库优化**
   - 配置连接池
   - 优化查询性能
   - 定期备份数据

### Docker部署

```dockerfile
# Dockerfile示例
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## 贡献指南

欢迎提交Issue和Pull Request来改进项目！

### 开发流程
1. Fork项目
2. 创建特性分支
3. 提交代码变更
4. 创建Pull Request

### 代码规范
- 遵循项目现有代码风格
- 添加必要的测试用例
- 更新相关文档

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目维护: IO性能测试平台开发团队
- 技术支持: support@io-platform.com
- 文档更新: docs@io-platform.com

---

**享受使用IO性能测试管理平台！** 🚀