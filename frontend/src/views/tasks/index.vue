<template>
  <div class="fade-in">
    <!-- 页面标题和操作 -->
    <div class="page-header">
      <div>
        <h1 class="page-title">任务</h1>
        <div class="page-subtitle">
          共 {{ totalTasks }} 个任务 ·
          <span class="text-warning">{{ runningTasks.length }} 运行中</span> ·
          <span class="text-muted">{{ pendingTasks.length }} 待执行</span> ·
          <span class="text-success">{{ completedTasks.length }} 已完成</span>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <el-button
          size="default"
          @click="handleBatchStart"
          :disabled="selectedTasks.length === 0 || !hasPendingTasks"
        >
          批量启动
        </el-button>
        <el-button
          size="default"
          @click="handleBatchStop"
          :disabled="selectedTasks.length === 0 || !hasRunningTasks"
        >
          批量停止
        </el-button>
        <el-button
          size="default"
          @click="handleBatchDelete"
          :disabled="selectedTasks.length === 0"
        >
          批量删除
        </el-button>
        <el-button type="primary" size="default" @click="showCreateDialog = true">
          创建任务
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="card p-4">
      <div class="flex flex-wrap items-center gap-4">
        <el-input
          v-model="searchQuery"
          placeholder="搜索任务名称"
          class="flex-1 min-w-64"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <MagnifyingGlassIcon class="w-4 h-4" />
          </template>
        </el-input>
        
        <el-select
          v-model="statusFilter"
          placeholder="状态筛选"
          class="w-32"
          clearable
          @change="handleSearch"
        >
          <el-option label="全部" value="" />
          <el-option label="待执行" value="pending" />
          <el-option label="运行中" value="running" />
          <el-option label="已完成" value="completed" />
          <el-option label="失败" value="failed" />
        </el-select>
        
        <el-button @click="handleSearch" type="primary">
          搜索
        </el-button>
        <el-button @click="resetFilters">
          重置
        </el-button>
      </div>
    </div>

    <!-- 任务列表 -->
    <div class="card">
      <el-table
        v-loading="loading"
        :data="filteredTasks"
        @selection-change="handleSelectionChange"
        style="width: 100%"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column label="任务名称" prop="task_name" min-width="200">
          <template #default="{ row }">
            <div class="flex items-center">
              <div>
                <div class="text-white font-medium">{{ row.task_name }}</div>
                <div v-if="row.description" class="text-sm text-slate-400">{{ row.description }}</div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="状态" prop="status" width="120">
          <template #default="{ row }">
            <div class="flex items-center">
              <div :class="getStatusDotClass(row.status)" class="w-3 h-3 rounded-full mr-2"></div>
              <span :class="getStatusClass(row.status)" class="status-tag">
                {{ getStatusText(row.status) }}
              </span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="用例" prop="test_case_name" width="150">
          <template #default="{ row }">
            <div class="text-slate-300">{{ row.test_case_name || '未知' }}</div>
          </template>
        </el-table-column>

        <el-table-column label="节点" prop="node_count" width="100">
          <template #default="{ row }">
            <div class="text-slate-300">{{ row.node_count || 0 }} 个</div>
          </template>
        </el-table-column>
        
        <el-table-column label="进度" width="120">
          <template #default="{ row }">
            <div v-if="row.status === 'running'">
              <el-progress
                :percentage="row.progress || 0"
                :status="row.progress === 100 ? 'success' : ''"
                :stroke-width="6"
              />
            </div>
            <div v-else class="text-slate-400">-</div>
          </template>
        </el-table-column>
        
        <el-table-column label="创建时间" prop="created_at" width="180">
          <template #default="{ row }">
            <div class="text-slate-300">{{ formatTime(row.created_at) }}</div>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <div class="flex space-x-1">
              <el-button
                v-if="row.status === 'pending'"
                type="success"
                size="small"
                @click="handleStart(row)"
                :loading="startLoading[row.id]"
              >
                启动
              </el-button>
              <el-button
                v-if="row.status === 'running'"
                type="warning"
                size="small"
                @click="handleStop(row)"
                :loading="stopLoading[row.id]"
              >
                停止
              </el-button>
              <el-button
                type="text"
                size="small"
                @click="$router.push(`/tasks/${row.id}`)"
              >
                详情
              </el-button>
              <el-dropdown trigger="click">
                <el-button type="text" size="small">
                  <EllipsisVerticalIcon class="w-4 h-4" />
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu class="bg-slate-800/95 backdrop-blur-sm border-slate-600/50">
                    <el-dropdown-item @click="handleViewLogs(row)">
                      <ClipboardDocumentIcon class="w-4 h-4 mr-2" />
                      查看日志
                    </el-dropdown-item>
                    <el-dropdown-item @click="handleViewMetrics(row)">
                      <ChartBarIcon class="w-4 h-4 mr-2" />
                      性能数据
                    </el-dropdown-item>
                    <el-dropdown-item divided @click="handleDelete(row)" class="text-danger-400">
                      <TrashIcon class="w-4 h-4 mr-2" />
                      删除
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
          共 {{ total }} 个任务
        </div>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="sizes, prev, pager, next"
          @size-change="handlePageChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 创建任务对话框 -->
    <TaskFormDialog
      v-model="showCreateDialog"
      @success="handleFormSuccess"
      @close="handleFormClose"
    />

    <!-- 任务日志对话框 -->
    <TaskLogsDialog
      v-model="showLogsDialog"
      :task="currentTask"
      :logs="currentLogs"
    />

    <!-- 性能数据对话框 -->
    <TaskMetricsDialog
      v-model="showMetricsDialog"
      :task="currentTask"
      :metrics="currentMetrics"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useTasksStore } from '@stores/tasks'
import { ElMessage, ElMessageBox } from 'element-plus'
import TaskFormDialog from './components/TaskFormDialog.vue'
import TaskLogsDialog from './components/TaskLogsDialog.vue'
import TaskMetricsDialog from './components/TaskMetricsDialog.vue'
import {
  PlusIcon,
  MagnifyingGlassIcon,
  EllipsisVerticalIcon,
  TrashIcon,
  ChartBarIcon,
  PlayIcon,
  ClockIcon,
  CheckCircleIcon
} from '@heroicons/vue/24/outline'

const tasksStore = useTasksStore()

// 状态
const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const selectedTasks = ref([])
const showCreateDialog = ref(false)
const showLogsDialog = ref(false)
const showMetricsDialog = ref(false)
const currentTask = ref(null)
const currentLogs = ref([])
const currentMetrics = ref([])
const startLoading = ref({})
const stopLoading = ref({})

// 计算属性
const filteredTasks = computed(() => tasksStore.filteredTasks)
const total = computed(() => tasksStore.total)
const totalTasks = computed(() => tasksStore.tasks.length)
const runningTasks = computed(() => tasksStore.runningTasks)
const pendingTasks = computed(() => tasksStore.pendingTasks)
const completedTasks = computed(() => tasksStore.completedTasks)

const hasPendingTasks = computed(() => {
  return selectedTasks.value.some(task => task.status === 'pending')
})

const hasRunningTasks = computed(() => {
  return selectedTasks.value.some(task => task.status === 'running')
})

// 获取状态点样式
const getStatusDotClass = (status) => {
  const classes = {
    pending: 'bg-slate-500',
    running: 'bg-warning-500',
    completed: 'bg-success-500',
    failed: 'bg-danger-500'
  }
  return classes[status] || 'bg-slate-500'
}

// 获取状态样式
const getStatusClass = (status) => {
  const classes = {
    pending: 'status-pending',
    running: 'status-running',
    completed: 'status-completed',
    failed: 'status-offline'
  }
  return classes[status] || 'status-pending'
}

// 获取状态文本
const getStatusText = (status) => {
  const texts = {
    pending: '待执行',
    running: '运行中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || '未知'
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return '未知'
  return new Date(time).toLocaleString('zh-CN')
}

// 搜索处理
const handleSearch = () => {
  tasksStore.setQueryParams({
    search: searchQuery.value,
    status_filter: statusFilter.value,
    page: currentPage.value,
    limit: pageSize.value
  })
  tasksStore.fetchTasks()
}

// 重置筛选
const resetFilters = () => {
  searchQuery.value = ''
  statusFilter.value = ''
  currentPage.value = 1
  pageSize.value = 10
  tasksStore.resetQueryParams()
  tasksStore.fetchTasks()
}

// 分页处理
const handlePageChange = () => {
  handleSearch()
}

// 选择变化处理
const handleSelectionChange = (selection) => {
  selectedTasks.value = selection
}

// 启动任务
const handleStart = async (task) => {
  startLoading.value[task.id] = true
  try {
    await tasksStore.startTask(task.id)
  } catch (error) {
    console.error('Start error:', error)
  } finally {
    startLoading.value[task.id] = false
  }
}

// 停止任务
const handleStop = async (task) => {
  stopLoading.value[task.id] = true
  try {
    await tasksStore.stopTask(task.id)
  } catch (error) {
    console.error('Stop error:', error)
  } finally {
    stopLoading.value[task.id] = false
  }
}

// 批量启动
const handleBatchStart = async () => {
  const pendingTasks = selectedTasks.value.filter(task => task.status === 'pending')
  if (pendingTasks.length === 0) return
  
  try {
    const taskIds = pendingTasks.map(task => task.id)
    await tasksStore.batchStartTasks(taskIds)
    selectedTasks.value = []
  } catch (error) {
    console.error('Batch start error:', error)
  }
}

// 批量停止
const handleBatchStop = async () => {
  const runningTasks = selectedTasks.value.filter(task => task.status === 'running')
  if (runningTasks.length === 0) return
  
  try {
    const taskIds = runningTasks.map(task => task.id)
    await tasksStore.batchStopTasks(taskIds)
    selectedTasks.value = []
  } catch (error) {
    console.error('Batch stop error:', error)
  }
}

// 删除任务
const handleDelete = async (task) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除任务 "${task.task_name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await tasksStore.deleteTask(task.id)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete error:', error)
    }
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedTasks.value.length === 0) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedTasks.value.length} 个任务吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const taskIds = selectedTasks.value.map(task => task.id)
    await tasksStore.batchDeleteTasks(taskIds)
    selectedTasks.value = []
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Batch delete error:', error)
    }
  }
}

// 查看日志
const handleViewLogs = async (task) => {
  currentTask.value = task
  try {
    await tasksStore.fetchTaskLogs(task.id)
    currentLogs.value = tasksStore.taskLogs
    showLogsDialog.value = true
  } catch (error) {
    console.error('Get logs error:', error)
  }
}

// 查看性能数据
const handleViewMetrics = async (task) => {
  currentTask.value = task
  try {
    await tasksStore.fetchTaskMetrics(task.id)
    currentMetrics.value = tasksStore.taskMetrics
    showMetricsDialog.value = true
  } catch (error) {
    console.error('Get metrics error:', error)
  }
}

// 表单成功处理
const handleFormSuccess = () => {
  showCreateDialog.value = false
  tasksStore.fetchTasks()
}

// 表单关闭处理
const handleFormClose = () => {
  // 清理状态
}

// 初始化
onMounted(() => {
  tasksStore.fetchTasks()
  tasksStore.connectWebSocket()
})

// 清理
onUnmounted(() => {
  tasksStore.disconnectWebSocket()
})
</script>

<style scoped>
.status-tag {
  @apply inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium;
}

.status-online {
  @apply bg-success-900/30 text-success-300 border border-success-700/50;
}

.status-offline {
  @apply bg-danger-900/30 text-danger-300 border border-danger-700/50;
}

.status-running {
  @apply bg-warning-900/30 text-warning-300 border border-warning-700/50;
}

.status-completed {
  @apply bg-success-900/30 text-success-300 border border-success-700/50;
}

.status-pending {
  @apply bg-slate-900/30 text-slate-300 border border-slate-700/50;
}

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