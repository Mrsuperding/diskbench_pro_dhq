# Bug 修复文档

## 基本信息

| 项目 | 内容 |
|------|------|
| **Bug ID** | BUG-2026-04-23-001 |
| **Bug 标题** | 管理员登录后刷新页面错误跳转到登录页 |
| **严重程度** | 高 (High) |
| **影响范围** | 登录模块 / 前端认证状态管理 |
| **发现日期** | 2026-04-23 |
| **修复状态** | ✅ 已修复 |

---

## 1. 问题描述

### 1.1 问题现象

管理员用户登录成功后跳转到 Dashboard 页面，但**刷新页面后错误地重定向到登录页**，而非保持在 Dashboard。

### 1.2 影响分析

- **用户体验**：登录后无法停留在目标页面，每次刷新都需要重新登录
- **影响用户**：所有登录用户都会遇到此问题
- **影响频率**：100%（每次刷新都会触发）

---

## 2. 根因分析

### 2.1 代码位置

```
frontend/src/stores/auth.js
```

### 2.2 问题代码

```javascript
export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token') || null,
    isAuthenticated: false,  // ❌ 问题所在：硬编码为 false
    loading: false
  }),
  // ...
})
```

### 2.3 根因说明

`isAuthenticated` 在 store 初始化时被硬编码为 `false`，即使 `localStorage` 中已存在有效的 token，也不会将用户识别为已认证状态。

当用户刷新页面时：
1. Vue 应用重新初始化
2. Router 的 `beforeEach` 守卫检查 `authStore.isAuthenticated`
3. 由于 `isAuthenticated` 始终为 `false`，路由守卫判定用户未登录
4. 强制重定向到 `/login`

### 2.4 数据流分析

```
页面刷新
   ↓
重新初始化 Vue 应用
   ↓
初始化 Pinia store (auth.js)
   ↓
state.isAuthenticated = false  ← 问题点
   ↓
Router beforeEach 守卫执行
   ↓
检查 isAuthenticated → false
   ↓
重定向到 /login  ← 问题结果
```

---

## 3. 修复方案

### 3.1 修复代码

```javascript
export const useAuthStore = defineStore('auth', {
  state: () => {
    const token = localStorage.getItem('token')
    return {
      user: null,
      token: token || null,
      isAuthenticated: !!token,  // ✅ 根据 token 是否存在来初始化
      loading: false
    }
  },
  // ...
})
```

### 3.2 修复说明

将 `isAuthenticated` 从硬编码 `false` 改为根据 `token` 是否存在来动态计算：
- 当 `token` 存在时 → `isAuthenticated = true`
- 当 `token` 不存在时 → `isAuthenticated = false`

### 3.3 修复后数据流

```
页面刷新
   ↓
重新初始化 Vue 应用
   ↓
初始化 Pinia store (auth.js)
   ↓
读取 localStorage.getItem('token')
   ↓
state.isAuthenticated = !!token  ← 修复点：自动推导认证状态
   ↓
Router beforeEach 守卫执行
   ↓
检查 isAuthenticated → true (如果有 token)
   ↓
允许访问目标页面  ← 正确结果
```

---

## 4. 测试验证

### 4.1 测试用例

| 用例ID | 用例名称 | 状态 |
|--------|----------|------|
| TC_UI_AUTH_007_01 | 管理员登录后刷新 Dashboard 应保持登录状态 | ✅ 通过 |
| TC_UI_AUTH_007_02 | localStorage 中存在 token 时刷新应保持认证状态 | ✅ 通过 |

### 4.2 验证步骤

```bash
# 1. 运行修复验证测试
pytest test/frontend/ui/test_login_timeout.py::TestLoginRefreshBugFix -v

# 2. 运行所有 UI 测试确保无回归
pytest test/frontend/ui/ -v
```

### 4.3 测试结果

```
36 passed in 64.67s
```

---

## 5. 修改文件清单

| 文件路径 | 修改类型 | 修改说明 |
|----------|----------|----------|
| `frontend/src/stores/auth.js` | 修复 | 修正 `isAuthenticated` 初始化逻辑 |

---

## 6. 关联知识

### 6.1 相关技术

- **框架**: Vue 3 + Pinia
- **路由**: Vue Router 4
- **状态管理**: Pinia Store

### 6.2 相关配置

- **Token 存储 Key**: `localStorage.token` (由 auth.js 第8行 `localStorage.getItem('token')` 读取)
- **Token 有效时间**: 30 分钟 (由后端 `ACCESS_TOKEN_EXPIRE_MINUTES` 配置)

### 6.3 潜在影响

此修复可能会影响以下场景：
- 首次访问时的初始认证状态判断
- Token 过期后的重定向行为

---

## 7. 后续建议

1. **统一 Token 存储 Key**：建议将 `auth.js` 中的 `token` 改为与 `utils/auth.js` 统一的 `diskbench_token`
2. **添加 Token 过期检测**：在刷新后主动检查 Token 是否过期，如过期则自动刷新
3. **添加单元测试**：为 auth store 添加 Vitest 单元测试，确保认证状态逻辑正确

---

## 8. 修复人员

| 角色 | 名称 | 日期 |
|------|------|------|
| 发现者 | AI Assistant | 2026-04-23 |
| 修复者 | AI Assistant | 2026-04-23 |
| 验证者 | AI Assistant | 2026-04-23 |

---

## 9. 变更记录

| 日期 | 版本 | 变更内容 | 变更人 |
|------|------|----------|--------|
| 2026-04-23 | 1.0 | 初始修复 | AI Assistant |
