import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
// 1. Element Plus 核心样式
import 'element-plus/dist/index.css'
// 2. 自定义全局样式（包含Tailwind）
import './style.css'
// 3. 登录页面专用样式
import '@/styles/login-cover.css'

// Element Plus
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

// 图标
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// Axios 全局配置 - 为所有直接使用 axios 的组件添加 auth header
import axios from 'axios'

// 从 localStorage 获取 token
const getToken = () => {
  return localStorage.getItem('token') || localStorage.getItem('diskbench_token') || ''
}

// 添加请求拦截器 - 为所有 axios 请求添加 Authorization header
axios.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 添加响应拦截器 - 处理 401 未授权错误
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token 过期或无效，清除本地存储并跳转到登录
      localStorage.removeItem('token')
      localStorage.removeItem('diskbench_token')
      localStorage.removeItem('diskbench_refresh_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

const app = createApp(App)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus, {
  locale: zhCn,
})

app.mount('#app')