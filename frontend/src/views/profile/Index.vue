<template>
  <div class="space-y-6 animate-fade-in">
    <!-- 页面标题 -->
    <div>
      <h2 class="text-2xl font-bold text-white">个人设置</h2>
      <p class="text-slate-400 mt-1">管理您的个人信息和偏好设置</p>
    </div>

    <!-- 用户信息卡片 -->
    <div class="card p-6">
      <div class="flex items-center space-x-6 mb-6">
        <div class="w-20 h-20 bg-primary-600 rounded-full flex items-center justify-center">
          <span class="text-2xl font-bold text-white">
            {{ authStore.username?.charAt(0).toUpperCase() || 'U' }}
          </span>
        </div>
        <div>
          <h3 class="text-xl font-semibold text-white">{{ authStore.username }}</h3>
          <p class="text-slate-400">{{ authStore.isAdmin ? '管理员' : '普通用户' }}</p>
          <p class="text-sm text-slate-500 mt-1">
            加入时间: {{ formatTime(userInfo.created_at) }}
          </p>
        </div>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="text-center">
          <div class="text-2xl font-bold text-white">{{ userStats.totalTasks }}</div>
          <div class="text-sm text-slate-400">总任务数</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-success-400">{{ userStats.completedTasks }}</div>
          <div class="text-sm text-slate-400">已完成任务</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-primary-400">{{ userStats.activeNodes }}</div>
          <div class="text-sm text-slate-400">活跃节点</div>
        </div>
      </div>
    </div>

    <!-- 设置选项 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 基本信息 -->
      <div class="card p-6">
        <h3 class="text-lg font-semibold text-white mb-4">基本信息</h3>
        <el-form
          ref="basicFormRef"
          :model="basicForm"
          :rules="basicRules"
          label-width="80px"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="basicForm.username"
              :disabled="true"
            />
          </el-form-item>
          
          <el-form-item label="邮箱" prop="email">
            <el-input
              v-model="basicForm.email"
              placeholder="请输入邮箱地址"
            />
          </el-form-item>
          
          <el-form-item label="昵称" prop="nickname">
            <el-input
              v-model="basicForm.nickname"
              placeholder="请输入昵称"
            />
          </el-form-item>
          
          <el-form-item label="电话" prop="phone">
            <el-input
              v-model="basicForm.phone"
              placeholder="请输入电话号码"
            />
          </el-form-item>
          
          <el-form-item label="部门" prop="department">
            <el-input
              v-model="basicForm.department"
              placeholder="请输入部门名称"
            />
          </el-form-item>
          
          <el-form-item>
            <el-button
              type="primary"
              @click="updateBasicInfo"
              :loading="updatingBasic"
            >
              保存更改
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 安全设置 -->
      <div class="card p-6">
        <h3 class="text-lg font-semibold text-white mb-4">安全设置</h3>
        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 rounded-lg bg-slate-700/30">
            <div>
              <div class="text-white font-medium">登录密码</div>
              <div class="text-sm text-slate-400">定期更换密码可以提高账户安全性</div>
            </div>
            <el-button
              type="primary"
              @click="showPasswordDialog = true"
            >
              修改密码
            </el-button>
          </div>
          
          <div class="flex items-center justify-between p-4 rounded-lg bg-slate-700/30">
            <div>
              <div class="text-white font-medium">两步验证</div>
              <div class="text-sm text-slate-400">开启后登录需要额外的验证码</div>
            </div>
            <el-switch
              v-model="securitySettings.twoFactorEnabled"
              active-text="已开启"
              inactive-text="未开启"
              @change="toggleTwoFactor"
            />
          </div>
          
          <div class="flex items-center justify-between p-4 rounded-lg bg-slate-700/30">
            <div>
              <div class="text-white font-medium">登录历史</div>
              <div class="text-sm text-slate-400">查看最近的登录活动</div>
            </div>
            <el-button
              type="text"
              @click="showLoginHistory = true"
            >
              查看详情
            </el-button>
          </div>
          
          <div class="flex items-center justify-between p-4 rounded-lg bg-slate-700/30">
            <div>
              <div class="text-white font-medium">API密钥</div>
              <div class="text-sm text-slate-400">用于API访问的密钥管理</div>
            </div>
            <el-button
              type="text"
              @click="showApiKeys = true"
            >
              管理密钥
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 偏好设置 -->
    <div class="card p-6">
      <h3 class="text-lg font-semibold text-white mb-4">偏好设置</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h4 class="text-white font-medium mb-3">界面设置</h4>
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-slate-300">暗黑模式</span>
              <el-switch
                v-model="preferences.darkMode"
                @change="toggleDarkMode"
              />
            </div>
            <div class="flex items-center justify-between">
              <span class="text-slate-300">紧凑布局</span>
              <el-switch
                v-model="preferences.compactLayout"
                @change="updatePreferences"
              />
            </div>
            <div class="flex items-center justify-between">
              <span class="text-slate-300">显示动画</span>
              <el-switch
                v-model="preferences.showAnimations"
                @change="updatePreferences"
              />
            </div>
          </div>
        </div>
        
        <div>
          <h4 class="text-white font-medium mb-3">通知设置</h4>
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-slate-300">邮件通知</span>
              <el-switch
                v-model="preferences.emailNotifications"
                @change="updatePreferences"
              />
            </div>
            <div class="flex items-center justify-between">
              <span class="text-slate-300">浏览器通知</span>
              <el-switch
                v-model="preferences.browserNotifications"
                @change="toggleBrowserNotifications"
              />
            </div>
            <div class="flex items-center justify-between">
              <span class="text-slate-300">任务完成通知</span>
              <el-switch
                v-model="preferences.taskNotifications"
                @change="updatePreferences"
              />
            </div>
            <div class="flex items-center justify-between">
              <span class="text-slate-300">告警通知</span>
              <el-switch
                v-model="preferences.alertNotifications"
                @change="updatePreferences"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 最近活动 -->
    <div class="card p-6">
      <h3 class="text-lg font-semibold text-white mb-4">最近活动</h3>
      <div class="space-y-3 max-h-64 overflow-y-auto">
        <div
          v-for="activity in recentActivities"
          :key="activity.id"
          class="flex items-center space-x-3 p-3 rounded-lg bg-slate-700/30"
        >
          <div :class="getActivityIconClass(activity.type)" class="w-8 h-8 rounded-full flex items-center justify-center">
            <component :is="getActivityIcon(activity.type)" class="w-4 h-4" />
          </div>
          <div class="flex-1">
            <div class="text-white font-medium">{{ activity.description }}</div>
            <div class="text-sm text-slate-400">{{ activity.timestamp }}</div>
          </div>
        </div>
      </div>
      
      <div v-if="recentActivities.length === 0" class="text-center py-8">
        <ClockIcon class="w-12 h-12 text-slate-600 mx-auto mb-2" />
        <p class="text-slate-400">暂无活动记录</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  UserIcon,
  KeyIcon,
  ClockIcon,
  CogIcon,
  BellIcon,
  MoonIcon,
  ComputerDesktopIcon,
  SparklesIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  InformationCircleIcon
} from '@heroicons/vue/24/outline'

const authStore = useAuthStore()

// 状态
const basicForm = ref({
  username: authStore.username,
  email: authStore.user?.email || '',
  nickname: authStore.user?.nickname || '',
  phone: authStore.user?.phone || '',
  department: authStore.user?.department || ''
})

const updatingBasic = ref(false)
const showPasswordDialog = ref(false)
const showLoginHistory = ref(false)
const showApiKeys = ref(false)

// 安全设置
const securitySettings = ref({
  twoFactorEnabled: false,
  loginHistory: []
})

// 偏好设置
const preferences = ref({
  darkMode: true,
  compactLayout: false,
  showAnimations: true,
  emailNotifications: true,
  browserNotifications: false,
  taskNotifications: true,
  alertNotifications: true
})

// 模拟数据
const userInfo = ref({
  id: authStore.userId,
  username: authStore.username,
  created_at: '2024-01-01 10:00:00',
  role: authStore.user?.role || 'user'
})

const userStats = ref({
  totalTasks: 25,
  completedTasks: 22,
  activeNodes: 3
})

const recentActivities = ref([
  {
    id: 1,
    type: 'task_completed',
    description: '完成了任务 "SSD性能测试"',
    timestamp: '2024-01-15 14:30:25'
  },
  {
    id: 2,
    type: 'node_added',
    description: '添加了新节点 "test-server-02"',
    timestamp: '2024-01-15 13:45:12'
  },
  {
    id: 3,
    type: 'case_created',
    description: '创建了新的测试用例 "NVMe基准测试"',
    timestamp: '2024-01-15 12:20:08'
  },
  {
    id: 4,
    type: 'login',
    description: '登录系统',
    timestamp: '2024-01-15 10:15:33'
  }
])

// 表单规则
const basicRules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  nickname: [
    { min: 2, max: 50, message: '昵称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ]
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return '未知'
  return new Date(time).toLocaleString('zh-CN')
}

// 更新基本信息
const updateBasicInfo = async () => {
  updatingBasic.value = true
  try {
    await authStore.updateUser(basicForm.value)
    ElMessage.success('基本信息更新成功')
  } catch (error) {
    console.error('Update basic info error:', error)
    ElMessage.error('更新失败')
  } finally {
    updatingBasic.value = false
  }
}

// 切换暗黑模式
const toggleDarkMode = () => {
  updatePreferences()
  // 这里可以添加切换主题的逻辑
  document.documentElement.classList.toggle('dark', preferences.value.darkMode)
}

// 切换浏览器通知
const toggleBrowserNotifications = () => {
  if (preferences.value.browserNotifications) {
    if ('Notification' in window) {
      Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
          ElMessage.success('浏览器通知已开启')
        } else {
          ElMessage.warning('浏览器通知权限被拒绝')
          preferences.value.browserNotifications = false
        }
      })
    } else {
      ElMessage.warning('浏览器不支持通知功能')
      preferences.value.browserNotifications = false
    }
  }
  updatePreferences()
}

// 更新偏好设置
const updatePreferences = () => {
  // 这里可以将偏好设置保存到服务器或本地存储
  localStorage.setItem('user_preferences', JSON.stringify(preferences.value))
  ElMessage.success('偏好设置已保存')
}

// 获取活动图标样式
const getActivityIconClass = (type) => {
  const classes = {
    task_completed: 'bg-success-600/20 text-success-400',
    node_added: 'bg-primary-600/20 text-primary-400',
    case_created: 'bg-warning-600/20 text-warning-400',
    login: 'bg-info-600/20 text-info-400',
    error: 'bg-danger-600/20 text-danger-400'
  }
  return classes[type] || 'bg-slate-600/20 text-slate-400'
}

// 获取活动图标
const getActivityIcon = (type) => {
  const icons = {
    task_completed: CheckCircleIcon,
    node_added: ComputerDesktopIcon,
    case_created: SparklesIcon,
    login: UserIcon,
    error: ExclamationCircleIcon
  }
  return icons[type] || InformationCircleIcon
}

// 初始化
onMounted(() => {
  // 加载保存的偏好设置
  const savedPreferences = localStorage.getItem('user_preferences')
  if (savedPreferences) {
    try {
      preferences.value = { ...preferences.value, ...JSON.parse(savedPreferences) }
    } catch (error) {
      console.error('Load preferences error:', error)
    }
  }
})
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>