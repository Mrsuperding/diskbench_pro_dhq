import { defineStore } from 'pinia'
import { authAPI } from '@api/auth'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

export const useAuthStore = defineStore('auth', {
  state: () => {
    const token = localStorage.getItem('token')
    return {
      user: null,
      token: token || null,
      isAuthenticated: !!token,  // FIX: 根据 token 是否存在来初始化认证状态
      loading: false
    }
  },

  getters: {
    isAdmin: (state) => {
      return state.user?.role === 'admin'
    },
    
    username: (state) => {
      return state.user?.username || ''
    },
    
    userId: (state) => {
      return state.user?.id || null
    }
  },

  actions: {
    // 用户登录
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

    // 用户注册
    async register(userData) {
      this.loading = true
      try {
        const response = await authAPI.register(userData)
        ElMessage.success('注册成功')
        return response
      } catch (error) {
        throw error
      } finally {
        this.loading = false
      }
    },

    // 获取用户信息
    async fetchUser() {
      try {
        const response = await authAPI.getCurrentUser()
        this.user = response
        this.isAuthenticated = true
        return response
      } catch (error) {
        this.logout()
        throw error
      }
    },

    // 更新用户信息
    async updateUser(userData) {
      try {
        const response = await authAPI.updateCurrentUser(userData)
        this.user = response
        ElMessage.success('用户信息更新成功')
        return response
      } catch (error) {
        throw error
      }
    },

    // 修改密码
    async changePassword(passwordData) {
      try {
        await authAPI.changePassword(passwordData)
        ElMessage.success('密码修改成功')
      } catch (error) {
        throw error
      }
    },

    // 用户登出
    async logout() {
      try {
        await authAPI.logout()
      } catch (error) {
        console.error('Logout error:', error)
      } finally {
        this.token = null
        this.user = null
        this.isAuthenticated = false
        localStorage.removeItem('token')
        ElMessage.success('已退出登录')
      }
    },

    // 检查认证状态
    async checkAuthStatus() {
      const token = localStorage.getItem('token')
      if (token) {
        this.token = token
        try {
          await this.fetchUser()
        } catch (error) {
          this.logout()
        }
      }
    },

    // 获取用户列表（管理员）
    async getUsers(params = {}) {
      try {
        return await authAPI.getUsers(params)
      } catch (error) {
        throw error
      }
    },

    // 更新用户角色（管理员）
    async updateUserRole(userId, role) {
      try {
        const response = await authAPI.updateUserRole(userId, { role })
        ElMessage.success('用户角色更新成功')
        return response
      } catch (error) {
        throw error
      }
    },

    // 更新用户状态（管理员）
    async updateUserStatus(userId, isActive) {
      try {
        const response = await authAPI.updateUserStatus(userId, { is_active: isActive })
        ElMessage.success('用户状态更新成功')
        return response
      } catch (error) {
        throw error
      }
    }
  }
})