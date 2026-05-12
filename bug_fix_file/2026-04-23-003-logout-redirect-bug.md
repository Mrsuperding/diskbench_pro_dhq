# Bug 修复文档

## 基本信息

| 项目 | 内容 |
|------|------|
| **Bug ID** | BUG-2026-04-23-003 |
| **Bug 标题** | 退出登录后无法跳转到登录页 |
| **严重程度** | 高 (High) |
| **影响范围** | 登录模块 / Store 状态不同步 |
| **发现日期** | 2026-04-23 |
| **修复状态** | ✅ 已修复 |

---

## 1. 问题描述

### 1.1 问题现象

管理员用户点击"退出登录"按钮后，系统未能正确跳转到登录页面，而是停留在当前页面或出现异常行为。

### 1.2 影响分析

- **用户体验**：退出登录后无法正确返回登录页，可能暴露已登录用户的信息
- **影响用户**：所有点击退出登录的用户
- **影响频率**：100%（每次退出都会触发）

---

## 2. 根因分析

### 2.1 代码位置

```
frontend/src/stores/user.js
frontend/src/stores/auth.js
frontend/src/components/UserDropdown.vue
frontend/src/router/index.js
```

### 2.2 问题代码

**UserDropdown.vue handleLogout()**:
```javascript
const handleLogout = async () => {
  dropdownOpen.value = false
  try {
    await userStore.logout()  // 调用 userStore.logout()
    router.push('/login')
    ElMessage.success('退出登录成功')
  } catch (error) {
    ElMessage.error('退出登录失败')
  }
}
```

**user.js logout() (修复前)**:
```javascript
async logout(options = {}) {
  const { skipApiCall = false } = options
  try {
    if (!skipApiCall && this.token) {
      await authAPI.logout()
    }
  } catch (error) {
    console.error('Logout error:', error)
  } finally {
    this.token = ''
    this.userInfo = null
    this.roles = []
    this.permissions = []
    removeToken()  // 只清除 userStore 的状态
  }
}
```

**router/index.js 路由守卫**:
```javascript
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()  // 使用 authStore，不是 userStore

  if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next('/')  // authStore.isAuthenticated 为 true 时重定向到 /
    return
  }
  next()
})
```

### 2.3 根因说明

存在**两个独立的 Store**：
- `authStore` (auth.js)：Login.vue 和 router.js 使用
- `userStore` (user.js)：UserDropdown 和 api/index.js 使用

当执行 `userStore.logout()` 时：
1. `userStore.token` 被清空
2. `userStore.userInfo` 被清空
3. `removeToken()` 清除了 `localStorage.diskbench_token`

但是 **`authStore.isAuthenticated` 仍然为 `true`**，因为：
- `authStore.logout()` 从未被调用
- `authStore.token` 和 `authStore.user` 未被清空
- localStorage 中的 `token` key 也未被清除

当 `UserDropdown` 调用 `router.push('/login')` 时：
1. 路由跳转到 `/login`
2. `/login` 路由的 `meta.requiresGuest: true`
3. Router `beforeEach` 守卫检查 `authStore.isAuthenticated`
4. 由于 `authStore.isAuthenticated` 仍为 `true`，守卫执行 `next('/')`
5. 用户被重定向到 `/` 而不是 `/login`

### 2.4 数据流分析

```
点击退出登录
   ↓
UserDropdown.handleLogout() → userStore.logout()
   ↓
user.js logout(): 清除 userStore.token, userInfo
   ↓
userStore 被清空，但 authStore 未被同步
   ↓
router.push('/login')
   ↓
Router beforeEach 守卫执行
   ↓
检查 authStore.isAuthenticated → true (未同步清除)
   ↓
to.meta.requiresGuest && isAuthenticated → true
   ↓
next('/')  ← 错误重定向到首页
```

---

## 3. 修复方案

### 3.1 修复代码

**frontend/src/stores/user.js**:
```javascript
import {defineStore} from 'pinia'
import {authAPI} from '@/api/auth'
import {setToken, setRefreshToken, getToken, removeToken} from '@/utils/auth'
import {useAuthStore} from '@/stores/auth'  // 导入 authStore

export const useUserStore = defineStore('user', {
    // ...
    actions: {
        async logout(options = {}) {
            const { skipApiCall = false } = options
            try {
                if (!skipApiCall && this.token) {
                    await authAPI.logout()
                }
            } catch (error) {
                console.error('Logout error:', error)
            } finally {
                this.token = ''
                this.userInfo = null
                this.roles = []
                this.permissions = []

                // 清除 token 和 refreshToken
                removeToken()

                // 同步清除 authStore 状态，确保路由守卫正确响应
                const authStore = useAuthStore()
                authStore.token = null
                authStore.user = null
                authStore.isAuthenticated = false
                localStorage.removeItem('token')
            }
        },
        // ...
    }
})
```

### 3.2 修复说明

在 `userStore.logout()` 中添加同步清除 `authStore` 状态的逻辑：
- 清除 `authStore.token`
- 清除 `authStore.user`
- 设置 `authStore.isAuthenticated = false`
- 清除 `localStorage.token`

### 3.3 修复后数据流

```
点击退出登录
   ↓
UserDropdown.handleLogout() → userStore.logout()
   ↓
user.js logout(): 清除 userStore 状态
   ↓
同步清除 authStore 状态 (token, user, isAuthenticated)
   ↓
localStorage.token 也被清除
   ↓
router.push('/login')
   ↓
Router beforeEach 守卫执行
   ↓
检查 authStore.isAuthenticated → false (已同步清除)
   ↓
to.meta.requiresGuest && isAuthenticated → false
   ↓
next() → 正常跳转到 /login
```

---

## 4. 测试验证

### 4.1 测试用例

| 用例ID | 用例名称 | 状态 |
|--------|----------|------|
| TC_UI_LOGOUT_001 | 管理员退出登录后应跳转到登录页 | ✅ 通过 |
| TC_UI_LOGOUT_002 | 退出登录后 authStore.isAuthenticated 应为 false | ✅ 通过 |
| TC_UI_LOGOUT_003 | 退出登录后 localStorage.token 应被清除 | ✅ 通过 |

### 4.2 验证步骤

```bash
# 1. 登录管理员账户
# 2. 点击退出登录按钮
# 3. 验证 URL 变为 /login
# 4. 验证页面显示登录表单
```

### 4.3 测试结果

```
退出登录后正确跳转到 /login
authStore.isAuthenticated = false
localStorage.token 已清除
```

---

## 5. 修改文件清单

| 文件路径 | 修改类型 | 修改说明 |
|----------|----------|----------|
| `frontend/src/stores/user.js` | 修复 | 在 logout 中同步清除 authStore 状态 |

---

## 6. 关联知识

### 6.1 相关技术

- **框架**: Vue 3 + Pinia
- **路由**: Vue Router 4
- **状态管理**: Pinia Store (双 Store 架构)

### 6.2 双 Store 设计分析

项目存在两个独立的 Store：

| Store | 文件 | 用途 | 使用组件 |
|-------|------|------|----------|
| authStore | stores/auth.js | 登录状态、路由守卫 | Login.vue, router.js |
| userStore | stores/user.js | 用户信息、API 请求 | UserDropdown, api/index.js |

这种设计导致状态不同步的问题，未来建议**合并为一个 UserStore**。

### 6.3 潜在影响

此修复确保了：
- 退出登录时 authStore 状态同步清除
- 路由守卫能正确响应认证状态
- 用户体验符合预期

---

## 7. 后续建议

1. **合并 Store**：将 authStore 和 userStore 合并为一个 userStore，避免状态不同步
2. **统一认证状态**：所有组件使用同一个 store 的认证状态
3. **添加单元测试**：为 logout 功能添加测试用例，确保状态正确清除

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