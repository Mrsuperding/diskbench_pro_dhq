# Bug 修复文档

## 基本信息

| 项目 | 内容 |
|------|------|
| **Bug ID** | BUG-2026-04-24-004 |
| **Bug 标题** | 登录后点击节点界面再点击 Dashboard 界面跳转到登录页 |
| **严重程度** | 高 (High) |
| **影响范围** | 登录模块 / Store 状态不同步 |
| **发现日期** | 2026-04-24 |
| **修复状态** | ✅ 已修复 |

---

## 1. 问题描述

### 1.1 问题现象

管理员用户登录成功后：
1. 点击侧边栏"节点"链接
2. 再点击侧边栏"概览/Dashboard"链接
3. 系统错误地跳转到登录页面，而非保持在 Dashboard

### 1.2 影响分析

- **用户体验**：登录后访问节点再返回 Dashboard 时被错误登出，体验不连贯
- **影响用户**：所有登录用户
- **影响频率**：100%（登录后访问节点再返回必然触发）

---

## 2. 根因分析

### 2.1 代码位置

```
frontend/src/stores/auth.js
frontend/src/stores/user.js
frontend/src/api/index.js
frontend/src/api/nodes.js
```

### 2.2 问题代码

**auth.js login 动作 (修复前)**:
```javascript
async login(credentials) {
  this.loading = true
  try {
    const response = await authAPI.login(credentials)
    this.token = response.access_token
    this.user = response.user
    this.isAuthenticated = true

    // 保存token到localStorage
    localStorage.setItem('token', this.token)

    ElMessage.success('登录成功')
    return response
  } catch (error) {
    throw error
  } finally {
    this.loading = false
  }
}
```

**user.js state (初始化)**:
```javascript
state: () => ({
    // 问题：只从 localStorage 初始化一次，登录前为空
    token: localStorage.getItem('token') || getToken() || '',
    userInfo: null,
    roles: [],
    permissions: []
}),
```

**api/index.js 请求拦截器**:
```javascript
api.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    const token = userStore.token  // 使用 userStore.token

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  ...
)
```

### 2.3 根因说明

存在 **Store 状态不同步** 问题：

**登录流程**:
1. `Login.vue` → `authStore.login()` → 存储 token 到 `localStorage.token`
2. `authStore.token` = JWT token
3. `authStore.isAuthenticated` = true
4. **但 `userStore.token` 从未被设置！**

**问题原因**:
1. `userStore` 在应用启动时初始化，此时 `localStorage.token` 为空
2. `userStore.token` = `''` (空字符串)
3. 登录成功后，`authStore.login()` 设置了 `localStorage.token`，但没有设置 `userStore.token`
4. `userStore.token` 在整个应用生命周期内保持为空，因为 Pinia store 的 state 只初始化一次

**节点页面访问流程**:
1. 用户点击"节点"链接
2. `nodes/Index.vue` 加载，`onMounted` 调用 `nodesStore.fetchNodes()`
3. `fetchNodes()` → `nodesAPI.getNodes()` → `api/index.js`
4. `api/index.js` 请求拦截器读取 `userStore.token`
5. `userStore.token` 为空，没有设置 Authorization header
6. 后端返回 **401 Unauthorized**
7. `api/index.js` 401 处理调用 `userStore.logout()`
8. `userStore.logout()` 清除 `authStore` 状态和 `localStorage.token`
9. 用户再点击 Dashboard 时，`authStore.isAuthenticated` 已为 false
10. 路由守卫重定向到 `/login`

### 2.4 数据流分析

```
登录流程 (修复前)
===============
Login.vue → authStore.login()
   ↓
authStore.state.token = JWT  ← 设置了
authStore.isAuthenticated = true  ← 设置了
localStorage.token = JWT  ← 设置了
   ↓
userStore.state.token = ''  ← 空！未设置！（只在初始化时读取一次）
userStore.userInfo = null  ← 空！

API 请求流程 (点击节点后)
=======================
nodes/Index.vue → nodesStore.fetchNodes()
   ↓
nodesAPI.getNodes() → api/index.js
   ↓
请求拦截器: userStore.token = '' (空！)
   ↓
没有 Authorization header
   ↓
后端返回 401 Unauthorized
   ↓
api/index.js 401 handler: userStore.logout()
   ↓
userStore.logout() 清除 authStore 状态
   ↓
localStorage.token = null
authStore.isAuthenticated = false
   ↓
用户再访问任何页面 → 路由守卫 authStore.isAuthenticated = false → 重定向到 /login
```

---

## 3. 修复方案

### 3.1 修复代码

**frontend/src/stores/auth.js**:
```javascript
import { defineStore } from 'pinia'
import { authAPI } from '@api/auth'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

export const useAuthStore = defineStore('auth', {
  // ...
  actions: {
    async login(credentials) {
      this.loading = true
      try {
        const response = await authAPI.login(credentials)
        this.token = response.access_token
        this.user = response.user
        this.isAuthenticated = true

        // 保存token到localStorage
        localStorage.setItem('token', this.token)

        // 同步更新 userStore.token，确保 API 请求能携带正确的 token
        const userStore = useUserStore()
        userStore.token = this.token
        userStore.userInfo = response.user || {}

        ElMessage.success('登录成功')
        return response
      } catch (error) {
        throw error
      } finally {
        this.loading = false
      }
    },
    // ...
  }
})
```

### 3.2 修复说明

在 `authStore.login()` 成功后，同步更新 `userStore` 的状态：
- `userStore.token = this.token` — 同步 token
- `userStore.userInfo = response.user` — 同步用户信息

这样后续 API 请求使用 `userStore.token` 时就能获取到正确的值。

### 3.3 修复后数据流

```
登录流程 (修复后)
===============
Login.vue → authStore.login()
   ↓
authStore.state.token = JWT  ← 设置了
authStore.isAuthenticated = true  ← 设置了
localStorage.token = JWT  ← 设置了
   ↓
userStore.token = JWT  ← 同步设置了！(新增)
userStore.userInfo = user  ← 同步设置了！(新增)

API 请求流程 (点击节点后)
=======================
nodes/Index.vue → nodesStore.fetchNodes()
   ↓
nodesAPI.getNodes() → api/index.js
   ↓
请求拦截器: userStore.token = JWT (有值！)
   ↓
Authorization: Bearer <JWT>
   ↓
后端返回 200 OK
   ↓
用户再访问任何页面 → authStore.isAuthenticated = true → 正常访问
```

---

## 4. 测试验证

### 4.1 测试用例

| 用例ID | 用例名称 | 状态 |
|--------|----------|------|
| TC_UI_NAV_001 | 登录后访问节点再访问 Dashboard 应保持登录状态 | ✅ 通过 |
| TC_UI_NAV_002 | 节点 API 请求不应返回 401 | ✅ 通过 |
| TC_UI_NAV_003 | 完整导航流程无认证丢失 | ✅ 通过 |

### 4.2 验证步骤

```bash
# 1. 登录管理员账户
# 2. 点击侧边栏"节点"链接
# 3. 验证 URL 变为 /nodes
# 4. 验证页面显示节点列表（无 401 错误）
# 5. 点击侧边栏"概览"链接
# 6. 验证 URL 变为 /dashboard
# 7. 验证保持在 Dashboard 而不是跳转到 /login
```

### 4.3 测试结果

```
登录后访问节点再访问 Dashboard - 通过
节点 API 请求返回 200 OK
导航流程无认证丢失
```

---

## 5. 修改文件清单

| 文件路径 | 修改类型 | 修改说明 |
|----------|----------|----------|
| `frontend/src/stores/auth.js` | 修复 | 登录成功后同步更新 userStore.token |

---

## 6. 关联知识

### 6.1 相关技术

- **框架**: Vue 3 + Pinia
- **路由**: Vue Router 4
- **HTTP 客户端**: Axios
- **状态管理**: Pinia Store (双 Store 架构)

### 6.2 双 Store 设计问题

项目存在两个独立的 Store：
- `authStore` (auth.js)：登录状态、路由守卫
- `userStore` (user.js)：用户信息、API 请求

这种设计导致状态不同步，需要手动同步。

### 6.3 潜在影响

此修复确保了：
- 登录后 userStore 状态被正确初始化
- API 请求携带正确的 Authorization header
- 导航流程中认证状态保持一致

---

## 7. 后续建议

1. **合并 Store**：将 authStore 和 userStore 合并为一个 userStore，避免状态不同步
2. **统一 token 管理**：确保所有组件使用同一个 store 的 token
3. **添加单元测试**：为登录流程添加测试，验证 userStore 状态正确

---

## 8. 修复人员

| 角色 | 名称 | 日期 |
|------|------|------|
| 发现者 | AI Assistant | 2026-04-24 |
| 修复者 | AI Assistant | 2026-04-24 |
| 验证者 | AI Assistant | 2026-04-24 |

---

## 9. 变更记录

| 日期 | 版本 | 变更内容 | 变更人 |
|------|------|----------|--------|
| 2026-04-24 | 1.0 | 初始修复 | AI Assistant |