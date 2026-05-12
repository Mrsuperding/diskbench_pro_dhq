# Bug 修复文档

## 基本信息

| 项目 | 内容 |
|------|------|
| **Bug ID** | BUG-2026-04-23-002 |
| **Bug 标题** | 节点页面 API 请求返回 401 Unauthorized |
| **严重程度** | 高 (High) |
| **影响范围** | 登录模块 / Token 存储不一致 |
| **发现日期** | 2026-04-23 |
| **修复状态** | ✅ 已修复 |

---

## 1. 问题描述

### 1.1 问题现象

管理员用户登录成功后访问节点管理页面 (`/nodes`)，页面控制台报错：
- `401 Unauthorized`
- `登录已过期，请重新登录`
- API 请求 `http://localhost:3000/api/nodes/?page=1&limit=10&status_filter=&search=` 返回 401

### 1.2 影响分析

- **用户体验**：登录后访问任何需要 API 数据的页面都会报错
- **影响用户**：所有登录用户都会遇到此问题
- **影响频率**：100%（只要访问需要 API 的页面）

---

## 2. 根因分析

### 2.1 代码位置

```
frontend/src/stores/user.js
frontend/src/stores/auth.js
frontend/src/utils/auth.js
frontend/src/views/auth/Login.vue
frontend/src/utils/request.js
```

### 2.2 问题代码

**auth.js (登录存储 token)**:
```javascript
// Login.vue 使用 authStore.login()
localStorage.setItem('token', this.token)  // 存储到 'token' key
```

**user.js (初始化读取 token)**:
```javascript
state: () => ({
    token: getToken() || '',  // 从 utils/auth.js 读取
    // ...
})
```

**utils/auth.js (getToken 实现)**:
```javascript
const TOKEN_KEY = 'diskbench_token'
export function getToken() {
  return localStorage.getItem(TOKEN_KEY)  // 从 'diskbench_token' 读取
}
```

**request.js (API 请求读取 token)**:
```javascript
const userStore = useUserStore()
if (userStore.token) {
    config.headers.Authorization = `Bearer ${userStore.token}`
}
```

### 2.3 根因说明

存在 **Token 存储 Key 不一致** 的问题：

| 组件 | 存储/读取 Key | 代码位置 |
|------|---------------|----------|
| `auth.js` (login) | `'token'` | `localStorage.setItem('token', ...)` |
| `utils/auth.js` (getToken) | `'diskbench_token'` | `localStorage.getItem('diskbench_token')` |
| `user.js` (state) | `'diskbench_token'` (通过 getToken) | `getToken()` |
| `request.js` | `'token'` (通过 userStore) | `userStore.token` |

**数据流断裂**：
1. `Login.vue` → `authStore.login()` → 存储到 `localStorage.token`
2. `request.js` → `userStore.token` → 读取 `user.js` state
3. `user.js` → `getToken()` → 读取 `localStorage.diskbench_token`
4. **结果**：`localStorage.token` 有值，但 `localStorage.diskbench_token` 为空
5. `request.js` 获取不到 token，API 请求无 Authorization header
6. 后端返回 **401 Unauthorized**

### 2.4 数据流分析

```
登录流程
========
Login.vue → authStore.login()
   ↓
auth.js: localStorage.setItem('token', this.token)  ← 存储到 'token' key
   ↓
localStorage = { 'token': 'xxx', 'diskbench_token': null }

API 请求流程
============
request.js: userStore.token
   ↓
user.js state: token = getToken()
   ↓
utils/auth.js: localStorage.getItem('diskbench_token')  ← 读取 'diskbench_token' key
   ↓
结果：获取到 null，但实际 token 存在 'token' key 中
   ↓
request.js 未设置 Authorization header
   ↓
后端返回 401 Unauthorized
```

---

## 3. 修复方案

### 3.1 修复代码

**frontend/src/stores/user.js**:
```javascript
import {defineStore} from 'pinia'
import {authAPI} from '@/api/auth'
import {setToken, setRefreshToken, getToken, removeToken} from '@/utils/auth'

export const useUserStore = defineStore('user', {
    state: () => ({
        // BUG FIX: auth.js 存储 token 到 'token' key，与 utils/auth.js 的 'diskbench_token' 不一致
        // 修复：统一从 'token' key 读取，与 auth.js 保持一致
        // 兼容：同时支持 'token' 和 'diskbench_token'，确保向后兼容
        token: localStorage.getItem('token') || getToken() || '',
        userInfo: null,
        roles: [],
        permissions: []
    }),
    // ...
})
```

### 3.2 修复说明

修改 `user.js` 的 state 初始化逻辑：
- **修复前**：`token: getToken() || ''` — 只从 `diskbench_token` 读取
- **修复后**：`token: localStorage.getItem('token') || getToken() || ''` — 优先从 `token` 读取，兼容 `diskbench_token`

### 3.3 修复后数据流

```
登录流程
========
Login.vue → authStore.login()
   ↓
auth.js: localStorage.setItem('token', this.token)
   ↓
localStorage = { 'token': 'xxx', 'diskbench_token': null }

API 请求流程
============
request.js: userStore.token
   ↓
user.js state: token = localStorage.getItem('token') || getToken()
   ↓
优先读取 'token' key → 获取到 'xxx'
   ↓
request.js 设置 Authorization: Bearer xxx
   ↓
后端返回 200 OK
```

---

## 4. 测试验证

### 4.1 测试用例

| 用例ID | 用例名称 | 状态 |
|--------|----------|------|
| TC_UI_NODES_006_01 | 节点 API 请求不应返回 401 | ✅ 通过 |
| TC_UI_NODES_006_02 | 所有 API 请求都有有效认证 | ✅ 通过 |
| TC_UI_NODES_006_03 | 完整登录流程后访问节点页面无 401 | ✅ 通过 |

### 4.2 验证步骤

```bash
# 1. 运行 API 认证测试
pytest test/frontend/ui/test_nodes_page.py::TestNodesPageAPIAuthorization -v

# 2. 运行所有 UI 测试确保无回归
pytest test/frontend/ui/ -v
```

### 4.3 测试结果

```
51 passed in 97.89s
```

---

## 5. 修改文件清单

| 文件路径 | 修改类型 | 修改说明 |
|----------|----------|----------|
| `frontend/src/stores/user.js` | 修复 | 修正 token 读取 key，优先读取 'token' |

---

## 6. 关联知识

### 6.1 相关技术

- **框架**: Vue 3 + Pinia
- **路由**: Vue Router 4
- **HTTP 客户端**: Axios
- **状态管理**: Pinia Store

### 6.2 Token 存储 Key 一览

| Key 名称 | 使用组件 | 用途 |
|----------|----------|------|
| `token` | auth.js | 登录时存储 access_token |
| `diskbench_token` | utils/auth.js | getToken() 读取 |
| `diskbench_refresh_token` | utils/auth.js | 存储 refresh_token |

### 6.3 潜在影响

此修复可能会影响：
- 之前直接使用 `diskbench_token` 的代码（但会 fallback 到 `token`）
- Token 刷新的相关逻辑

---

## 7. 后续建议

1. **统一 Token 存储 Key**：删除冗余的 `diskbench_token`，统一使用 `token`
2. **添加单元测试**：为 auth store 和 user store 添加单元测试，确保 token 存储/读取逻辑正确
3. **Token 刷新优化**：确保 refresh token 也使用统一的 key
4. **代码审查**：检查是否有其他地方使用不同的 token key

---

## 8. 修复人员

| 角色 | 名称 | 日期 |
|------|------|------|
| 发现者 | 用户反馈 (管理员访问节点页面 401) | 2026-04-23 |
| 修复者 | AI Assistant | 2026-04-23 |
| 验证者 | AI Assistant | 2026-04-23 |

---

## 9. 变更记录

| 日期 | 版本 | 变更内容 | 变更人 |
|------|------|----------|--------|
| 2026-04-23 | 1.0 | 初始修复 | AI Assistant |
