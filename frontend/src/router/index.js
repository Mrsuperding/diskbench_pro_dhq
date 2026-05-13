import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@views/auth/Login.vue'),
    meta: { requiresGuest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@views/auth/Register.vue'),
    meta: { requiresGuest: true },
  },
  {
    path: '/',
    name: 'Layout',
    // 使用新的极简 layouts/index.vue
    component: () => import('@/layouts/index.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/dashboard',
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@views/dashboard/Index.vue'),
        meta: { title: '概览' },
      },

      // 资源
      { path: 'nodes', component: () => import('@views/nodes/Index.vue'), meta: { title: '节点' } },
      { path: 'cases', component: () => import('@views/cases/Index.vue'), meta: { title: '用例' } },
      { path: 'cases/:id', component: () => import('@views/cases/Detail.vue'), meta: { title: '用例详情' } },

      // 测试
      { path: 'tasks', component: () => import('@views/tasks/Index.vue'), meta: { title: '任务' } },
      { path: 'tasks/:id', component: () => import('@views/tasks/Detail.vue'), meta: { title: '任务详情' } },
      { path: 'schedules', component: () => import('@views/schedules/index.vue'), meta: { title: '定时调度' } },
      { path: 'run-batches', component: () => import('@views/run-batches/index.vue'), meta: { title: '运行批次' } },
      { path: 'baselines', component: () => import('@views/baselines/index.vue'), meta: { title: '性能基准' } },

      // 运维
      { path: 'monitor', component: () => import('@views/monitor/Index.vue'), meta: { title: '实时监控' } },
      { path: 'alerts', component: () => import('@views/alerts/index.vue'), meta: { title: '告警' } },
      { path: 'audit-logs', component: () => import('@views/audit-logs/index.vue'), meta: { title: '审计日志' } },
      { path: 'logs', component: () => import('@views/logs/Index.vue'), meta: { title: '日志' } },

      // 系统
      { path: 'users', component: () => import('@views/users/Index.vue'), meta: { title: '用户管理', requiresAdmin: true } },
      { path: 'profile', component: () => import('@views/profile/Index.vue'), meta: { title: '个人设置' } },
      { path: 'settings', component: () => import('@views/profile/Index.vue'), meta: { title: '设置' } },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@views/error/404.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
    return
  }
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next('/')
    return
  }
  if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next('/')
    return
  }
  next()
})

export default router
