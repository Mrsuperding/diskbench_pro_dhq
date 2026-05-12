import axios from 'axios'
import {ElMessage} from 'element-plus'
import {useUserStore} from '@/stores/user'
import router from '@/router'
import {getToken, setToken, setRefreshToken, getRefreshToken, removeToken} from '@/utils/auth'
import {refreshToken as refreshTokenAPI} from '@/utils/auth'

const request = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
    timeout: 10000
})

// 请求拦截器
request.interceptors.request.use(
    config => {
        const userStore = useUserStore()
        if (userStore.token) {
            config.headers.Authorization = `Bearer ${userStore.token}`
        }
        return config
    },
    error => Promise.reject(error)
)

// 响应拦截器
let refreshing = false
let requests = []
request.interceptors.response.use(
    response => response.data,
    async error => {
        const originalRequest = error.config

        // 处理 401 错误（token 过期）
        if (error.response?.status === 401 && !originalRequest._retry) {
            if (refreshing) {
                // 如果正在刷新 token，将请求加入队列
                return new Promise(resolve => {
                    requests.push(() => resolve(request(originalRequest)))
                })
            }

            originalRequest._retry = true
            refreshing = true

            try {
                // 获取刷新 token
                const refreshTokenStr = getRefreshToken()
                if (!refreshTokenStr) {
                    throw new Error('没有刷新 token')
                }

                // 调用刷新 token API
                const response = await refreshTokenAPI(refreshTokenStr)
                const newToken = response.access_token

                // 更新 token
                setToken(newToken)
                if (response.refresh_token) {
                    setRefreshToken(response.refresh_token)
                }

                // 重试队列中的请求
                requests.forEach(cb => cb())
                requests = []

                // 重试当前请求
                originalRequest.headers.Authorization = `Bearer ${newToken}`
                return request(originalRequest)
            } catch (err) {
                // 刷新 token 失败，需要重新登录
                ElMessage.error('登录已过期，请重新登录')
                const userStore = useUserStore()
                userStore.logout({ skipApiCall: true }).then(() => {
                    router.push('/login')
                })
                return Promise.reject(err)
            } finally {
                refreshing = false
            }
        }

        // 处理其他错误
        ElMessage.error(error.response?.data?.message || '请求失败')
        return Promise.reject(error)
    }
)

export default request