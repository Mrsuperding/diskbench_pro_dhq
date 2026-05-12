# 修改后端端口指南

## 概述

本文档说明如何修改后端服务端口，包括后端代码配置和前端代理配置。

---

## 1. 修改后端端口

### 1.1 查找后端入口文件

后端入口文件通常是 `main.py` 或 `app.py`，位于项目根目录或 `backend` 目录下。

### 1.2 修改端口配置

编辑后端入口文件，找到 `uvicorn.run()` 或 `app.run()` 调用：

```python
# 原始配置 (端口 8000)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

修改为新端口：

```python
# 修改为新端口 (例如 5003)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=5003, reload=True)
```

### 1.3 如果使用环境变量

```python
import os

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 5003))  # 默认 5003
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
```

---

## 2. 修改前端代理配置

### 2.1 找到 Vite 配置文件

前端项目中的 `vite.config.js` 或 `vite.config.ts`

### 2.2 修改代理目标

```javascript
// 原始配置
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',  // 修改这里
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '/api')
    }
  }
}
```

修改为新端口：

```javascript
// 修改后
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:5003',  // 新端口
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '/api')
    }
  }
}
```

---

## 3. 修改前端 WebSocket 连接地址

除了 API 代理配置，前端还有多个 WebSocket 连接地址需要修改：

### 3.1 Socket.IO 连接地址

文件：`frontend/src/stores/websocket.js`

```javascript
// 原始配置
const connectionUrl = ref('http://localhost:8000')

// 修改后
const connectionUrl = ref('http://localhost:5003')
```

### 3.2 任务 Store WebSocket

文件：`frontend/src/stores/tasks.js`

```javascript
// 原始配置
const wsUrl = `ws://localhost:8000/api/monitor/ws`

// 修改后
const wsUrl = `ws://localhost:5003/api/monitor/ws`
```

### 3.3 监控 Store WebSocket

文件：`frontend/src/stores/monitor.js`

```javascript
// 原始配置
const wsUrl = `ws://localhost:8000/api/monitor/ws`

// 修改后
const wsUrl = `ws://localhost:5003/api/monitor/ws`
```

### 3.4 监控页面 WebSocket

文件：`frontend/src/views/monitor/useMonitor.vue`

```javascript
// 原始配置
ws = new WebSocket('ws://localhost:8000/ws')

// 修改后
ws = new WebSocket('ws://localhost:5003/ws')
```

---

## 4. 重启服务

### 4.1 重启后端

停止当前后端服务，然后重新启动：

```bash
# 停止 (Ctrl+C)
python -m uvicorn app.main:app --host 0.0.0.0 --port 5003
```

### 4.2 重启前端

```bash
# 停止 (Ctrl+C)
cd frontend
npm run dev
```

### 4.3 验证配置

1. 访问前端页面 `http://localhost:3000`
2. 打开浏览器 DevTools (F12)
3. 切换到 Network 标签
4. 刷新页面，确认 API 请求和 WebSocket 连接都发送到新端口

---

## 5. 常见问题

### Q: 修改后端端口后前端报 404 或 500 错误？

**检查项：**
1. 后端服务是否正在新端口运行
2. 前端 Vite 代理配置是否指向正确的端口
3. 前端是否已重启（Vite 配置更改需要重启）
4. WebSocket 连接地址是否已更新

### Q: 如何查看当前后端运行在哪个端口？

```bash
# Windows
netstat -ano | findstr "LISTENING"

# 或检查任务管理器中的 Python 进程
```

### Q: WebSocket 连接失败？

**检查项：**
1. 确认所有 WebSocket 地址都已更新（搜索 `localhost:8000`）
2. 确认后端 WebSocket 服务已启动
3. 刷新浏览器或重启前端服务

### Q: 多个后端服务同时运行冲突？

确保只运行一个后端实例，或者每个使用不同端口。

---

## 6. 本次修改记录

| 日期 | 修改内容 | 旧端口 | 新端口 |
|------|---------|--------|--------|
| 2026-05-07 | 后端端口 | 8000 | 5003 |
| 2026-05-07 | 前端 API 代理 | 8000 | 5003 |
| 2026-05-07 | 前端 WebSocket | 8000 | 5003 |

---

## 7. 相关文件路径

### 后端文件
- 后端入口: `D:\delvelop_project\ai_project\diskbench_pro\app\main.py`

### 前端文件
- Vite 配置: `D:\delvelop_project\ai_project\diskbench_pro\frontend\vite.config.js`
- WebSocket Store: `D:\delvelop_project\ai_project\diskbench_pro\frontend\src\stores\websocket.js`
- 任务 Store: `D:\delvelop_project\ai_project\diskbench_pro\frontend\src\stores\tasks.js`
- 监控 Store: `D:\delvelop_project\ai_project\diskbench_pro\frontend\src\stores\monitor.js`
- 监控页面: `D:\delvelop_project\ai_project\diskbench_pro\frontend\src\views\monitor\useMonitor.vue`