<!-- src/components/UserDropdown.vue -->
<template>
  <div class="user-dropdown">
    <button class="user-btn" @click="toggleDropdown">
      <div class="user-avatar">
        <img
          v-if="userStore.userInfo?.avatar"
          :src="userStore.userInfo.avatar"
          alt="用户头像"
        >
        <div v-else class="avatar-placeholder">
          <i class="fa fa-user"></i>
        </div>
      </div>
      <div class="user-info" v-if="!dropdownOpen">
        <div class="user-name">{{ userStore.userInfo?.username || '用户名' }}</div>
        <div class="user-role">{{ userStore.userInfo?.role || '普通用户' }}</div>
      </div>
      <i class="fa fa-angle-down dropdown-icon" :class="{ 'rotate': dropdownOpen }"></i>
    </button>

    <div class="dropdown-menu" :class="{ 'show': dropdownOpen }">
      <div class="dropdown-menu-header">
        <div class="header-avatar">
          <img
            v-if="userStore.userInfo?.avatar"
            :src="userStore.userInfo.avatar"
            alt="用户头像"
          >
          <div v-else class="header-avatar-placeholder">
            <i class="fa fa-user"></i>
          </div>
        </div>
        <div class="header-info">
          <div class="header-name">{{ userStore.userInfo?.username || '用户名' }}</div>
          <div class="header-email">{{ userStore.userInfo?.email || 'user@example.com' }}</div>
        </div>
      </div>

      <div class="dropdown-menu-divider"></div>

      <div class="dropdown-menu-item" @click="handleProfile">
        <i class="fa fa-user-circle"></i>
        <span>个人资料</span>
      </div>

      <div class="dropdown-menu-item" @click="handleSettings">
        <i class="fa fa-cog"></i>
        <span>设置</span>
      </div>

      <div class="dropdown-menu-divider"></div>

      <div class="dropdown-menu-item logout-item" @click="handleLogout">
        <i class="fa fa-sign-out"></i>
        <span>退出登录</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const router = useRouter()
const dropdownOpen = ref(false)

// 切换下拉菜单
const toggleDropdown = () => {
  dropdownOpen.value = !dropdownOpen.value
}

// 点击其他地方关闭下拉菜单
document.addEventListener('click', (e) => {
  const dropdown = document.querySelector('.user-dropdown')
  if (dropdown && !dropdown.contains(e.target)) {
    dropdownOpen.value = false
  }
})

// 处理个人资料点击
const handleProfile = () => {
  dropdownOpen.value = false
  // 可以跳转到个人资料页面
  ElMessage.info('个人资料功能待实现')
}

// 处理设置点击
const handleSettings = () => {
  dropdownOpen.value = false
  router.push('/settings')
}

// 处理退出登录
const handleLogout = async () => {
  dropdownOpen.value = false
  try {
    await userStore.logout()
    router.push('/login')
    ElMessage.success('退出登录成功')
  } catch (error) {
    ElMessage.error('退出登录失败')
    console.error('Logout error:', error)
  }
}
</script>

<style scoped>
.user-dropdown {
  position: relative;
}

.user-btn {
  display: flex;
  align-items: center;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0 8px;
  height: 40px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.user-btn:hover {
  background-color: #f0f0f0;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  margin-right: 8px;
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  background-color: #e0e0e0;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.user-info {
  text-align: left;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.user-role {
  font-size: 12px;
  color: #999;
}

.dropdown-icon {
  margin-left: 8px;
  font-size: 14px;
  color: #666;
  transition: transform 0.2s;
}

.dropdown-icon.rotate {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: 48px;
  right: 0;
  width: 240px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
  overflow: hidden;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-8px);
  transition: all 0.2s;
}

.dropdown-menu.show {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.dropdown-menu-header {
  padding: 16px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #f0f0f0;
}

.header-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  margin-right: 12px;
}

.header-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.header-avatar-placeholder {
  width: 100%;
  height: 100%;
  background-color: #e0e0e0;
  color: #666;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.header-info {
  flex: 1;
}

.header-name {
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.header-email {
  font-size: 12px;
  color: #999;
}

.dropdown-menu-divider {
  height: 1px;
  background-color: #f0f0f0;
}

.dropdown-menu-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  font-size: 14px;
  color: #333;
  cursor: pointer;
  transition: background-color 0.2s;
}

.dropdown-menu-item:hover {
  background-color: #f5f5f5;
}

.dropdown-menu-item i {
  margin-right: 8px;
  color: #666;
  width: 20px;
  text-align: center;
}

.logout-item {
  color: #ff4d4f;
}

.logout-item i {
  color: #ff4d4f;
}
</style>
