<template>
  <div class="space-y-6 animate-fade-in">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-white">用户管理</h2>
        <p class="text-slate-400 mt-1">管理系统用户和权限</p>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div class="card p-6">
        <div class="flex items-center">
          <div class="p-3 rounded-lg bg-primary-600/20">
            <UsersIcon class="w-6 h-6 text-primary-400" />
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-slate-400">总用户数</p>
            <p class="text-2xl font-bold text-white">{{ totalUsers }}</p>
          </div>
        </div>
      </div>

      <div class="card p-6">
        <div class="flex items-center">
          <div class="p-3 rounded-lg bg-success-600/20">
            <UserIcon class="w-6 h-6 text-success-400" />
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-slate-400">活跃用户</p>
            <p class="text-2xl font-bold text-white">{{ activeUsers }}</p>
          </div>
        </div>
      </div>

      <div class="card p-6">
        <div class="flex items-center">
          <div class="p-3 rounded-lg bg-warning-600/20">
            <ShieldCheckIcon class="w-6 h-6 text-warning-400" />
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-slate-400">管理员</p>
            <p class="text-2xl font-bold text-white">{{ adminUsers }}</p>
          </div>
        </div>
      </div>

      <div class="card p-6">
        <div class="flex items-center">
          <div class="p-3 rounded-lg bg-danger-600/20">
            <NoSymbolIcon class="w-6 h-6 text-danger-400" />
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-slate-400">禁用用户</p>
            <p class="text-2xl font-bold text-white">{{ inactiveUsers }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 用户列表 -->
    <div class="card">
      <div class="p-6 border-b border-slate-700/50">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold text-white">用户列表</h3>
          <div class="flex items-center space-x-3">
            <el-input
              v-model="searchQuery"
              placeholder="搜索用户名或邮箱"
              class="w-64"
              clearable
              @clear="fetchUsers"
              @keyup.enter="fetchUsers"
            >
              <template #prefix>
                <MagnifyingGlassIcon class="w-4 h-4" />
              </template>
            </el-input>
            <el-button type="primary" @click="showCreateDialog = true">
              <PlusIcon class="w-4 h-4 mr-1" />
              添加用户
            </el-button>
          </div>
        </div>
      </div>
      
      <el-table
        v-loading="loading"
        :data="filteredUsers"
        style="width: 100%"
      >
        <el-table-column label="用户" prop="username" min-width="200">
          <template #default="{ row }">
            <div class="flex items-center">
              <div class="w-10 h-10 bg-primary-600 rounded-full flex items-center justify-center mr-3">
                <span class="text-white font-medium">
                  {{ row.username?.charAt(0).toUpperCase() || 'U' }}
                </span>
              </div>
              <div>
                <div class="text-white font-medium">{{ row.username }}</div>
                <div class="text-sm text-slate-400">{{ row.email }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="角色" prop="role" width="120">
          <template #default="{ row }">
            <el-tag
              size="small"
              :type="row.role === 'admin' ? 'warning' : 'info'"
            >
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="状态" prop="is_active" width="100">
          <template #default="{ row }">
            <el-tag
              size="small"
              :type="row.is_active ? 'success' : 'danger'"
            >
              {{ row.is_active ? '活跃' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="创建时间" prop="created_at" width="180">
          <template #default="{ row }">
            <div class="text-slate-300">{{ formatTime(row.created_at) }}</div>
          </template>
        </el-table-column>
        
        <el-table-column label="最后登录" prop="last_login" width="180">
          <template #default="{ row }">
            <div class="text-slate-300">{{ formatTime(row.last_login) }}</div>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <div class="flex space-x-2">
              <el-button
                type="primary"
                size="small"
                @click="handleEdit(row)"
              >
                编辑
              </el-button>
              <el-dropdown trigger="click">
                <el-button type="text" size="small">
                  <EllipsisVerticalIcon class="w-4 h-4" />
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu class="bg-slate-800/95 backdrop-blur-sm border-slate-600/50">
                    <el-dropdown-item @click="handleToggleRole(row)">
                      <ShieldCheckIcon class="w-4 h-4 mr-2" />
                      {{ row.role === 'admin' ? '取消管理员' : '设为管理员' }}
                    </el-dropdown-item>
                    <el-dropdown-item @click="handleToggleStatus(row)">
                      <PowerIcon class="w-4 h-4 mr-2" />
                      {{ row.is_active ? '禁用用户' : '启用用户' }}
                    </el-dropdown-item>
                    <el-dropdown-item divided @click="handleDelete(row)" class="text-danger-400">
                      <TrashIcon class="w-4 h-4 mr-2" />
                      删除用户
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="flex items-center justify-between p-4 border-t border-slate-700/50">
        <div class="text-sm text-slate-400">
          共 {{ totalUsers }} 个用户
        </div>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="totalUsers"
          :page-sizes="[10, 20, 50, 100]"
          layout="sizes, prev, pager, next"
          @size-change="fetchUsers"
          @current-change="fetchUsers"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  UsersIcon,
  UserIcon,
  ShieldCheckIcon,
  NoSymbolIcon,
  MagnifyingGlassIcon,
  EllipsisVerticalIcon,
  TrashIcon,
  PowerIcon,
  PlusIcon
} from '@heroicons/vue/24/outline'

const authStore = useAuthStore()

// 状态
const loading = ref(false)
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const showCreateDialog = ref(false)

// 模拟数据
const users = ref([
  {
    id: 1,
    username: 'admin',
    email: 'admin@example.com',
    role: 'admin',
    is_active: true,
    created_at: '2024-01-01 10:00:00',
    last_login: '2024-01-15 14:30:25'
  },
  {
    id: 2,
    username: 'demo',
    email: 'demo@example.com',
    role: 'user',
    is_active: true,
    created_at: '2024-01-02 09:15:30',
    last_login: '2024-01-14 16:45:12'
  },
  {
    id: 3,
    username: 'testuser',
    email: 'test@example.com',
    role: 'user',
    is_active: false,
    created_at: '2024-01-03 11:20:45',
    last_login: null
  }
])

// 计算属性
const totalUsers = computed(() => users.value.length)
const activeUsers = computed(() => users.value.filter(u => u.is_active).length)
const adminUsers = computed(() => users.value.filter(u => u.role === 'admin').length)
const inactiveUsers = computed(() => users.value.filter(u => !u.is_active).length)

const filteredUsers = computed(() => {
  if (!searchQuery.value) {
    return users.value
  }
  
  const search = searchQuery.value.toLowerCase()
  return users.value.filter(user =>
    user.username.toLowerCase().includes(search) ||
    user.email.toLowerCase().includes(search)
  )
})

// 格式化时间
const formatTime = (time) => {
  if (!time) return '从未'
  return new Date(time).toLocaleString('zh-CN')
}

// 获取用户列表
const fetchUsers = async () => {
  loading.value = true
  try {
    // 这里应该调用API获取用户列表
    // 实际项目中需要根据后端API进行调整
    await new Promise(resolve => setTimeout(resolve, 500))
  } catch (error) {
    console.error('Fetch users error:', error)
  } finally {
    loading.value = false
  }
}

// 编辑用户
const handleEdit = (user) => {
  // 这里可以打开编辑对话框
  ElMessage.info('编辑功能开发中')
}

// 切换用户角色
const handleToggleRole = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要${user.role === 'admin' ? '取消管理员权限' : '设为管理员'}吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await authStore.updateUserRole(user.id, user.role === 'admin' ? 'user' : 'admin')
    await fetchUsers()
    
    ElMessage.success('用户角色更新成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Toggle role error:', error)
    }
  }
}

// 切换用户状态
const handleToggleStatus = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要${user.is_active ? '禁用' : '启用'}该用户吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await authStore.updateUserStatus(user.id, !user.is_active)
    await fetchUsers()
    
    ElMessage.success('用户状态更新成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Toggle status error:', error)
    }
  }
}

// 删除用户
const handleDelete = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await authStore.deleteUser(user.id)
    await fetchUsers()
    
    ElMessage.success('用户删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete error:', error)
    }
  }
}

// 初始化
onMounted(() => {
  fetchUsers()
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