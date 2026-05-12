import {defineStore} from 'pinia'
import {authAPI} from '@/api/auth'
import {setToken, setRefreshToken, getToken, removeToken} from '@/utils/auth'
import {useAuthStore} from '@/stores/auth'

export const useUserStore = defineStore('user', {
    state: () => ({
        // BUG FIX: auth.js 存储 token 到 'token' key，与 utils/auth.js 的 'diskbench_token' 不一致
        // 修复：统一从 'token' key 读取，与 auth.js 保持一致
        token: localStorage.getItem('token') || getToken() || '',
        userInfo: null,
        roles: [],
        permissions: []
    }),

    getters: {
        isAuthenticated: (state) => !!state.token,
        userId: (state) => state.userInfo?.id,
        username: (state) => state.userInfo?.username,
        avatar: (state) => state.userInfo?.avatar
    },

    actions: {
        // frontend/src/stores/user.js
        async login(loginForm) {
            try {
                const response = await authAPI.login(loginForm)

                // 根据后端实际返回的数据结构提取信息
                const token = response.access_token
                const refreshToken = response.refresh_token
                const userInfo = response.user || {}

                if (!token) {
                    throw new Error('登录失败：未获取到 access_token')
                }

                this.token = token
                this.userInfo = userInfo
                // 将 role 字符串转换为 roles 数组
                this.roles = userInfo.role ? [userInfo.role] : []
                this.permissions = [] // 如果需要权限，可以从 userInfo 中提取

                setToken(token)
                if (refreshToken) {
                    setRefreshToken(refreshToken)
                }
                return Promise.resolve(response)
            } catch (error) {
                console.error('Login error:', error)
                return Promise.reject(error)
            }
        },

        async getUserInfo() {
            try {
                const response = await authAPI.getCurrentUser()
                const userInfo = response.user || {}

                this.userInfo = userInfo
                this.roles = userInfo.role ? [userInfo.role] : []
                this.permissions = [] // 如果需要权限，可以从 userInfo 中提取

                return Promise.resolve(response)
            } catch (error) {
                return Promise.reject(error)
            }
        },

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

        hasPermission(permission) {
            return this.permissions.includes(permission)
        },

        hasRole(role) {
            return this.roles.includes(role)
        }
    }
})