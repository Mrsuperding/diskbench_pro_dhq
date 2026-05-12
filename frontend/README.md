# IO性能测试管理平台前端

一个现代化的IO性能测试管理平台前端应用，基于Vue.js 3构建。

## 功能特性

### 🎯 核心功能
- **用户认证** - 完整的登录、注册、权限管理系统
- **节点管理** - 分布式测试节点的管理和监控
- **用例管理** - IO测试用例的创建、编辑和执行
- **任务管理** - 测试任务的调度和执行管理
- **实时监控** - 实时性能数据监控和可视化
- **数据分析** - 详细的测试报告和性能分析

### 🎨 用户体验
- **响应式设计** - 完美适配桌面和移动设备
- **现代化UI** - 基于Element Plus的专业界面设计
- **流畅动画** - 使用Anime.js提供优雅的交互动画
- **实时更新** - WebSocket实时数据推送
- **数据可视化** - ECharts图表展示性能数据

### ⚡ 技术特性
- **Vue 3 Composition API** - 现代化的Vue.js开发模式
- **Pinia状态管理** - 高效的状态管理方案
- **Vue Router 4** - 强大的路由管理
- **TypeScript支持** - 类型安全的开发体验
- **模块化架构** - 清晰的项目结构和代码组织

## 技术栈

### 核心框架
- **Vue.js 3** - 渐进式JavaScript框架
- **Vue Router 4** - 官方路由管理器
- **Pinia** - 直观的状态管理库

### UI组件库
- **Element Plus** - 基于Vue 3的组件库
- **Tailwind CSS** - 实用优先的CSS框架

### 数据可视化
- **ECharts.js** - 强大的图表库
- **Vue-ECharts** - ECharts的Vue封装

### 实时通信
- **Socket.io** - 实时双向通信
- **WebSocket** - 原生WebSocket支持

### 工具库
- **Axios** - HTTP客户端
- **Anime.js** - 轻量级动画库
- **Day.js** - 日期处理库
- **Lodash** - 实用工具库

## 快速开始

### 环境要求
- Node.js >= 16.0.0
- npm >= 8.0.0

### 安装依赖
```bash
npm install
```

### 开发模式
```bash
npm run dev
```

### 生产构建
```bash
npm run build
```

### 预览构建结果
```bash
npm run preview
```

## 项目结构

```
src/
├── api/           # API接口定义
├── assets/        # 静态资源
├── components/    # 可复用组件
├── composables/   # 组合式函数
├── router/        # 路由配置
├── stores/        # Pinia状态管理
├── utils/         # 工具函数
├── views/         # 页面组件
├── App.vue        # 根组件
├── main.js        # 应用入口
└── style.css      # 全局样式
```

## 核心模块

### 1. 认证模块 (auth)
- 用户登录/注册
- JWT令牌管理
- 权限控制
- 用户信息管理

### 2. 节点管理 (nodes)
- 节点注册和发现
- 节点状态监控
- 节点配置管理
- 负载均衡

### 3. 用例管理 (testcases)
- 测试用例CRUD
- 用例模板管理
- 参数配置
- 用例版本控制

### 4. 任务管理 (tasks)
- 任务创建和调度
- 执行状态跟踪
- 任务队列管理
- 结果收集

### 5. 实时监控 (monitoring)
- 实时数据推送
- 性能指标展示
- 图表可视化
- 告警通知

## 配置说明

### 环境变量
创建 `.env` 文件配置环境变量：

```env
# API基础URL
VITE_API_BASE_URL=http://localhost:8000

# WebSocket URL
VITE_WS_URL=ws://localhost:8000

# 应用标题
VITE_APP_TITLE=IO性能测试平台
```

### 后端API集成
项目假设后端API遵循RESTful设计规范：

- **认证接口**
  - POST `/api/auth/login` - 用户登录
  - POST `/api/auth/register` - 用户注册
  - POST `/api/auth/logout` - 用户登出
  - GET `/api/auth/profile` - 获取用户信息

- **节点管理接口**
  - GET `/api/nodes` - 获取节点列表
  - POST `/api/nodes` - 创建节点
  - GET `/api/nodes/{id}` - 获取节点详情
  - PUT `/api/nodes/{id}` - 更新节点
  - DELETE `/api/nodes/{id}` - 删除节点

- **用例管理接口**
  - GET `/api/testcases` - 获取用例列表
  - POST `/api/testcases` - 创建用例
  - GET `/api/testcases/{id}` - 获取用例详情
  - PUT `/api/testcases/{id}` - 更新用例
  - DELETE `/api/testcases/{id}` - 删除用例

- **任务管理接口**
  - GET `/api/tasks` - 获取任务列表
  - POST `/api/tasks` - 创建任务
  - GET `/api/tasks/{id}` - 获取任务详情
  - PUT `/api/tasks/{id}` - 更新任务
  - DELETE `/api/tasks/{id}` - 删除任务

- **实时监控接口**
  - WebSocket `/ws/monitoring` - 实时数据推送
  - GET `/api/metrics/{task_id}` - 获取任务指标

## 部署指南

### 静态部署
```bash
npm run build
```
构建后的文件位于 `dist/` 目录，可部署到任何静态文件服务器。

### Docker部署
```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 生产环境配置
1. 配置HTTPS证书
2. 设置反向代理
3. 配置CDN加速
4. 启用Gzip压缩
5. 设置安全头

## 开发规范

### 代码风格
- 使用ESLint进行代码检查
- 使用Prettier进行代码格式化
- 遵循Vue.js风格指南

### Git规范
- 使用语义化提交信息
- 遵循Git Flow分支策略
- 代码审查要求

### 组件设计
- 单一职责原则
-  props验证
- 事件命名规范
- 样式作用域

## 性能优化

### 构建优化
- 代码分割和懒加载
- Tree Shaking
- 图片压缩
- 字体优化

### 运行时优化
- 虚拟滚动
- 防抖和节流
- 缓存策略
- 内存管理

## 浏览器支持

| 浏览器 | 版本 |
|--------|------|
| Chrome | 90+  |
| Firefox | 88+  |
| Safari | 14+  |
| Edge | 90+  |

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请通过以下方式联系：
- 邮箱: support@io-platform.com
- 文档: https://docs.io-platform.com
- 社区: https://community.io-platform.com

---

**享受使用IO性能测试管理平台！** 🚀