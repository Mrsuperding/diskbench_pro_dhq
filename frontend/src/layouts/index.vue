<!--
  DiskBench Pro · 主布局（极简版）
  ==================================
  - 侧边栏：窄（200px）、浅色、无图标背景色块、一目了然的菜单分组
  - 顶栏：标题 + 搜索 + 暗色切换 + 用户，一条线搞定
  - 内容区：白底 surface，最大宽度不限（适配大屏）
  - 去掉：FontAwesome、毛玻璃、深紫色系、动态粒子等装饰
  - 支持：折叠侧边栏 / 暗色模式切换 / 记住折叠状态到 localStorage
-->
<template>
  <div class="app-shell" :class="{ 'sidebar-collapsed': collapsed }">
    <!-- ========== 侧边栏 ========== -->
    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-logo">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" />
            <path d="M12 8v4l3 3" stroke-linecap="round" />
          </svg>
        </div>
        <span v-if="!collapsed" class="brand-text">DiskBench</span>
      </div>

      <nav class="sidebar-nav">
        <template v-for="group in navGroups" :key="group.id">
          <div v-if="group.title && !collapsed" class="nav-group-title">
            {{ group.title }}
          </div>
          <router-link
            v-for="item in group.items"
            :key="item.path"
            :to="item.path"
            class="nav-item"
            :class="{ active: isActive(item.path) }"
            :title="collapsed ? item.label : ''"
          >
            <component :is="item.icon" class="nav-icon" />
            <span v-if="!collapsed" class="nav-label">{{ item.label }}</span>
          </router-link>
        </template>
      </nav>

      <button class="sidebar-collapse-btn" @click="toggleCollapse">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline :points="collapsed ? '9 6 15 12 9 18' : '15 6 9 12 15 18'" />
        </svg>
      </button>
    </aside>

    <!-- ========== 主区域 ========== -->
    <div class="main">
      <header class="topbar">
        <Breadcrumb class="topbar-breadcrumb" />
        <div class="topbar-actions">
          <button class="icon-btn" @click="toggleDark" :title="dark ? '切换到浅色' : '切换到深色'">
            <!-- sun / moon 图标内联 SVG -->
            <svg v-if="dark" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="4" />
              <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
            </svg>
            <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          </button>
          <UserDropdown />
        </div>
      </header>

      <main class="content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" class="fade-in" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, h } from 'vue'
import { useRoute } from 'vue-router'
import Breadcrumb from '@/components/Breadcrumb.vue'
import UserDropdown from '@/components/UserDropdown.vue'

const route = useRoute()

// ===== 折叠状态（持久化到 localStorage）=====
const collapsed = ref(localStorage.getItem('sidebar_collapsed') === '1')
const toggleCollapse = () => {
  collapsed.value = !collapsed.value
  localStorage.setItem('sidebar_collapsed', collapsed.value ? '1' : '0')
}

// ===== 暗色模式 =====
const dark = ref(false)
const applyDark = (on) => {
  document.documentElement.classList.toggle('dark', on)
}
const toggleDark = () => {
  dark.value = !dark.value
  localStorage.setItem('theme', dark.value ? 'dark' : 'light')
  applyDark(dark.value)
}
onMounted(() => {
  const saved = localStorage.getItem('theme')
  dark.value = saved === 'dark'
  applyDark(dark.value)
})

// ===== 判断菜单激活（支持子路径匹配）=====
const isActive = (path) => {
  if (path === '/dashboard') return route.path === '/' || route.path === '/dashboard'
  return route.path === path || route.path.startsWith(path + '/')
}

// ===== 内联 SVG 图标组件（避免引 FontAwesome）=====
const mkIcon = (paths) => ({
  render() {
    return h('svg', {
      viewBox: '0 0 24 24', width: 18, height: 18,
      fill: 'none', stroke: 'currentColor',
      'stroke-width': 1.8, 'stroke-linecap': 'round', 'stroke-linejoin': 'round',
    }, paths.map(d => h('path', { d })))
  },
})
const DashboardIcon = mkIcon(['M3 13h8V3H3v10zM13 21h8V11h-8v10zM3 21h8v-6H3v6zM13 3v6h8V3h-8z'])
const NodeIcon      = mkIcon(['M3 5h18v4H3zM3 15h18v4H3z', 'M7 7h.01M7 17h.01'])
const CaseIcon      = mkIcon(['M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z',
                              'M14 2v6h6', 'M9 13h6M9 17h6M9 9h1'])
const TaskIcon      = mkIcon(['M9 11l3 3L22 4', 'M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11'])
const MonitorIcon   = mkIcon(['M3 12h4l3-9 4 18 3-9h4'])
const ScheduleIcon  = mkIcon(['M3 4h18v18H3zM3 10h18', 'M8 2v4M16 2v4'])
const BaselineIcon  = mkIcon(['M3 12h3l3-9 4 18 3-9h5'])
const AlertIcon     = mkIcon(['M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z',
                              'M12 9v4', 'M12 17h.01'])
const AuditIcon     = mkIcon(['M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2',
                              'M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM23 21v-2a4 4 0 0 0-3-3.87',
                              'M16 3.13a4 4 0 0 1 0 7.75'])
const LogIcon       = mkIcon(['M4 4h16v16H4z', 'M4 9h16M9 4v16'])
const SettingsIcon  = mkIcon(['M12 1v4m0 14v4M4.22 4.22l2.83 2.83m9.9 9.9l2.83 2.83M1 12h4m14 0h4M4.22 19.78l2.83-2.83m9.9-9.9l2.83-2.83',
                              'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z'])

// ===== 菜单结构 =====
const navGroups = [
  {
    id: 'overview',
    items: [
      { path: '/dashboard', label: '概览', icon: DashboardIcon },
    ],
  },
  {
    id: 'resource',
    title: '资源',
    items: [
      { path: '/nodes', label: '节点', icon: NodeIcon },
      { path: '/cases', label: '用例', icon: CaseIcon },
    ],
  },
  {
    id: 'test',
    title: '测试',
    items: [
      { path: '/tasks',      label: '任务',     icon: TaskIcon },
      { path: '/schedules',  label: '调度',     icon: ScheduleIcon },
      { path: '/run-batches',label: '批次',     icon: TaskIcon },
      { path: '/baselines',  label: '基准',     icon: BaselineIcon },
    ],
  },
  {
    id: 'ops',
    title: '运维',
    items: [
      { path: '/monitor',     label: '监控',     icon: MonitorIcon },
      { path: '/alerts',      label: '告警',     icon: AlertIcon },
      { path: '/audit-logs',  label: '审计',     icon: AuditIcon },
      { path: '/logs',        label: '日志',     icon: LogIcon },
    ],
  },
  {
    id: 'sys',
    title: '系统',
    items: [
      { path: '/settings', label: '设置', icon: SettingsIcon },
    ],
  },
]
</script>

<style scoped>
/* ============================================================
   布局骨架
   ============================================================ */
.app-shell {
  display: flex;
  min-height: 100vh;
  background: var(--bg);
}

/* ============================================================
   侧边栏 —— 窄、浅色、无装饰
   ============================================================ */
.sidebar {
  position: relative;
  width: 200px;
  flex: 0 0 200px;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  transition: width .2s ease, flex-basis .2s ease;
}
.sidebar-collapsed .sidebar {
  width: 60px;
  flex-basis: 60px;
}

.sidebar-brand {
  height: 56px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 16px;
  border-bottom: 1px solid var(--border-2);
}
.brand-logo {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: var(--brand);
  color: #fff;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.brand-text {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: .02em;
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: 8px 6px;
}

.nav-group-title {
  padding: 14px 10px 6px;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-3);
  text-transform: uppercase;
  letter-spacing: .06em;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  margin: 2px 0;
  border-radius: var(--radius);
  color: var(--text-2);
  font-size: 13.5px;
  text-decoration: none;
  transition: background .12s, color .12s;
  white-space: nowrap;
  overflow: hidden;
}
.nav-item:hover {
  background: var(--surface-2);
  color: var(--text);
}
.nav-item.active {
  background: var(--brand-soft);
  color: var(--brand);
  font-weight: 500;
}
.nav-icon {
  flex-shrink: 0;
  width: 18px; height: 18px;
}

/* 折叠状态下的菜单项居中显示图标 */
.sidebar-collapsed .nav-item { justify-content: center; padding: 8px; }
.sidebar-collapsed .sidebar-brand { padding: 0; justify-content: center; }

.sidebar-collapse-btn {
  position: absolute;
  right: -12px;
  top: 68px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text-2);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 5;
  transition: color .12s, border-color .12s;
}
.sidebar-collapse-btn:hover { color: var(--brand); border-color: var(--brand); }

/* ============================================================
   主区域 —— 顶栏 + 内容
   ============================================================ */
.main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.topbar {
  height: 56px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  gap: 16px;
}
.topbar-breadcrumb { flex: 1; min-width: 0; }
.topbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon-btn {
  width: 32px;
  height: 32px;
  border-radius: var(--radius);
  border: none;
  background: transparent;
  color: var(--text-2);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  transition: background .12s, color .12s;
}
.icon-btn:hover { background: var(--surface-2); color: var(--text); }

.content {
  flex: 1;
  padding: 20px 24px;
  overflow-y: auto;
}

/* 路由切换过渡 */
.fade-enter-active, .fade-leave-active { transition: opacity .15s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* 小屏响应式 */
@media (max-width: 768px) {
  .sidebar { position: fixed; left: 0; top: 0; height: 100%; z-index: 20; }
  .sidebar-collapse-btn { display: none; }
  .content { padding: 12px; }
}
</style>
