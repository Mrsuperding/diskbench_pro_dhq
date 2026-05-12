<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
    <!-- 顶部导航 -->
    <header class="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700/50 fixed top-0 left-0 right-0 z-50">
      <div class="px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <!-- Logo和菜单切换 -->
          <div class="flex items-center">
            <button
              @click="toggleSidebar"
              class="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700/50 lg:hidden"
            >
              <Bars3Icon class="w-6 h-6" />
            </button>
            
            <div class="flex items-center ml-4 lg:ml-0">
              <div class="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"></path>
                </svg>
              </div>
              <span class="ml-3 text-lg font-semibold text-white hidden sm:block">IO性能测试平台</span>
            </div>
          </div>

          <!-- 右侧菜单 -->
          <div class="flex items-center space-x-4">
            <!-- 全屏切换 -->
            <button
              @click="toggleFullscreen"
              class="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700/50"
            >
              <ArrowsPointingOutIcon v-if="!isFullscreen" class="w-5 h-5" />
              <ArrowsPointingInIcon v-else class="w-5 h-5" />
            </button>

            <!-- 用户菜单 -->
            <el-dropdown trigger="click">
              <div class="flex items-center space-x-3 cursor-pointer p-2 rounded-lg hover:bg-slate-700/50">
                <div class="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
                  <span class="text-sm font-medium text-white">
                    {{ authStore.username?.charAt(0).toUpperCase() || 'U' }}
                  </span>
                </div>
                <div class="hidden md:block">
                  <div class="text-sm font-medium text-white">{{ authStore.username }}</div>
                  <div class="text-xs text-slate-400">{{ authStore.isAdmin ? '管理员' : '普通用户' }}</div>
                </div>
              </div>
              
              <template #dropdown>
                <el-dropdown-menu class="bg-slate-800/95 backdrop-blur-sm border-slate-600/50">
                  <el-dropdown-item @click="$router.push('/profile')">
                    <UserIcon class="w-4 h-4 mr-2" />
                    个人设置
                  </el-dropdown-item>
                  <el-dropdown-item v-if="authStore.isAdmin" @click="$router.push('/users')">
                    <UsersIcon class="w-4 h-4 mr-2" />
                    用户管理
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="handleLogout">
                    <ArrowLeftOnRectangleIcon class="w-4 h-4 mr-2" />
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </header>

    <!-- 侧边栏 -->
    <aside
      :class="[
        'fixed left-0 top-16 bottom-0 w-64 bg-slate-800/50 backdrop-blur-sm border-r border-slate-700/50 z-40 transition-transform duration-300 lg:translate-x-0',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      ]"
    >
      <nav class="p-4 space-y-2">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          :class="[
            'flex items-center px-4 py-3 rounded-lg text-sm font-medium transition-colors duration-200',
            $route.path === item.path
              ? 'bg-primary-600 text-white'
              : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
          ]"
        >
          <component :is="item.icon" class="w-5 h-5 mr-3" />
          {{ item.title }}
        </router-link>
      </nav>
    </aside>

    <!-- 主内容区 -->
    <main class="lg:pl-64 pt-16 min-h-screen">
      <div class="p-4 sm:p-6 lg:p-8">
        <!-- 页面标题 -->
        <div class="mb-6" v-if="$route.meta.title">
          <h1 class="text-2xl font-bold text-white">{{ $route.meta.title }}</h1>
          <p class="text-slate-400 mt-1">{{ $route.meta.description }}</p>
        </div>

        <!-- 路由内容 -->
        <router-view />
      </div>
    </main>

    <!-- 移动端侧边栏遮罩 -->
    <div
      v-if="sidebarOpen"
      @click="toggleSidebar"
      class="fixed inset-0 bg-black/50 z-30 lg:hidden"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '@stores/auth'
import { 
  Bars3Icon,
  ArrowsPointingOutIcon,
  ArrowsPointingInIcon,
  UserIcon,
  UsersIcon,
  ArrowLeftOnRectangleIcon,
  HomeIcon,
  ServerIcon,
  DocumentTextIcon,
  ClipboardDocumentListIcon,
  ChartBarIcon,
  CogIcon
} from '@heroicons/vue/24/outline'

const authStore = useAuthStore()
const sidebarOpen = ref(false)
const isFullscreen = ref(false)

// 菜单项
const menuItems = computed(() => [
  { path: '/', title: '仪表板', icon: HomeIcon },
  { path: '/nodes', title: '节点管理', icon: ServerIcon },
  { path: '/cases', title: '用例管理', icon: DocumentTextIcon },
  { path: '/tasks', title: '任务管理', icon: ClipboardDocumentListIcon },
  { path: '/monitor', title: '实时监控', icon: ChartBarIcon }
])

// 切换侧边栏
const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value
}

// 切换全屏
const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
    isFullscreen.value = true
  } else {
    document.exitFullscreen()
    isFullscreen.value = false
  }
}

// 退出登录
const handleLogout = async () => {
  await authStore.logout()
  window.location.reload()
}
</script>

<style scoped>
/* 确保侧边栏在移动端正确显示 */
@media (max-width: 1024px) {
  .lg\\:pl-64 {
    padding-left: 0;
  }
}
</style>