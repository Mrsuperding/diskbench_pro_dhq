<template>
  <el-dialog
    v-model="visible"
    :title="`任务日志 - ${task?.name || '未知任务'}`"
    width="900px"
    class="logs-dialog"
    @close="handleClose"
  >
    <div class="space-y-4">
      <!-- 日志控制 -->
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <el-button
            type="primary"
            size="small"
            @click="refreshLogs"
            :loading="refreshing"
          >
            <ArrowPathIcon class="w-4 h-4 mr-1" />
            刷新
          </el-button>
          <el-checkbox
            v-model="autoRefresh"
            label="自动刷新"
            @change="toggleAutoRefresh"
          />
          <el-select
            v-model="logLevel"
            size="small"
            class="w-32"
            placeholder="日志级别"
          >
            <el-option label="全部" value="" />
            <el-option label="INFO" value="info" />
            <el-option label="WARNING" value="warning" />
            <el-option label="ERROR" value="error" />
            <el-option label="DEBUG" value="debug" />
          </el-select>
        </div>
        <div class="flex items-center space-x-2">
          <el-button
            type="text"
            size="small"
            @click="copyLogs"
          >
            <ClipboardDocumentIcon class="w-4 h-4 mr-1" />
            复制全部
          </el-button>
          <el-button
            type="text"
            size="small"
            @click="downloadLogs"
          >
            <ArrowDownTrayIcon class="w-4 h-4 mr-1" />
            下载日志
          </el-button>
        </div>
      </div>

      <!-- 日志内容 -->
      <div class="logs-container">
        <div
          v-if="filteredLogs.length > 0"
          ref="logsContainer"
          class="logs-content max-h-96 overflow-y-auto p-4 bg-slate-900/50 rounded-lg font-mono text-sm"
        >
          <div
            v-for="(log, index) in filteredLogs"
            :key="index"
            class="log-entry mb-1"
            :class="getLogLevelClass(log.level)"
          >
            <span class="log-timestamp">{{ formatTime(log.timestamp) }}</span>
            <span class="log-level">[{{ log.level.toUpperCase() }}]</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
        
        <div v-else class="text-center py-12">
          <ClipboardDocumentIcon class="w-12 h-12 text-slate-600 mx-auto mb-2" />
          <p class="text-slate-400">暂无日志数据</p>
          <p class="text-sm text-slate-500 mt-1">任务执行后会产生日志</p>
        </div>
      </div>

      <!-- 日志统计 -->
      <div v-if="logs.length > 0" class="bg-slate-700/30 p-4 rounded-lg">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div class="text-2xl font-bold text-white">{{ logs.length }}</div>
            <div class="text-sm text-slate-400">总日志数</div>
          </div>
          <div>
            <div class="text-2xl font-bold text-info-400">{{ countLogsByLevel('info') }}</div>
            <div class="text-sm text-slate-400">INFO</div>
          </div>
          <div>
            <div class="text-2xl font-bold text-warning-400">{{ countLogsByLevel('warning') }}</div>
            <div class="text-sm text-slate-400">WARNING</div>
          </div>
          <div>
            <div class="text-2xl font-bold text-danger-400">{{ countLogsByLevel('error') }}</div>
            <div class="text-sm text-slate-400">ERROR</div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end space-x-3">
        <el-button @click="handleClose">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ArrowPathIcon,
  ClipboardDocumentIcon,
  ArrowDownTrayIcon
} from '@heroicons/vue/24/outline'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  task: {
    type: Object,
    default: null
  },
  logs: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'close'])

// 状态
const refreshing = ref(false)
const autoRefresh = ref(false)
const logLevel = ref('')
const autoRefreshTimer = ref(null)

// 本地日志数据
const logs = ref([])

// 计算属性
const filteredLogs = computed(() => {
  if (!logLevel.value) {
    return logs.value
  }
  return logs.value.filter(log => log.level === logLevel.value)
})

// 对话框可见性
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 监听props变化
watch(() => props.logs, (newLogs) => {
  logs.value = newLogs || []
}, { immediate: true })

// 获取日志级别样式
const getLogLevelClass = (level) => {
  const classes = {
    info: 'log-info',
    warning: 'log-warning',
    error: 'log-error',
    debug: 'log-debug'
  }
  return classes[level] || 'log-info'
}

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleTimeString('zh-CN')
}

// 统计日志数量
const countLogsByLevel = (level) => {
  return logs.value.filter(log => log.level === level).length
}

// 刷新日志
const refreshLogs = async () => {
  refreshing.value = true
  try {
    // 这里应该调用API获取最新日志
    // 实际项目中需要根据后端API进行调整
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('日志刷新成功')
  } catch (error) {
    ElMessage.error('日志刷新失败')
  } finally {
    refreshing.value = false
  }
}

// 切换自动刷新
const toggleAutoRefresh = () => {
  if (autoRefresh.value) {
    autoRefreshTimer.value = setInterval(() => {
      refreshLogs()
    }, 5000) // 每5秒刷新一次
  } else {
    if (autoRefreshTimer.value) {
      clearInterval(autoRefreshTimer.value)
      autoRefreshTimer.value = null
    }
  }
}

// 复制日志
const copyLogs = async () => {
  try {
    const logText = logs.value.map(log => 
      `${formatTime(log.timestamp)} [${log.level.toUpperCase()}] ${log.message}`
    ).join('\n')
    
    await navigator.clipboard.writeText(logText)
    ElMessage.success('日志已复制到剪贴板')
  } catch (error) {
    console.error('Copy failed:', error)
    ElMessage.error('复制失败')
  }
}

// 下载日志
const downloadLogs = () => {
  const logText = logs.value.map(log => 
    `${formatTime(log.timestamp)} [${log.level.toUpperCase()}] ${log.message}`
  ).join('\n')
  
  const blob = new Blob([logText], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `task-${props.task?.id || 'unknown'}-logs.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
  emit('close')
}

// 清理
onUnmounted(() => {
  if (autoRefreshTimer.value) {
    clearInterval(autoRefreshTimer.value)
  }
})
</script>

<style scoped>
.logs-dialog {
  @apply bg-slate-800/95 backdrop-blur-sm border-slate-600/50;
}

.logs-dialog :deep(.el-dialog__title) {
  @apply text-white;
}

.logs-content {
  @apply font-mono text-sm;
}

.log-entry {
  @apply flex items-start space-x-2;
}

.log-timestamp {
  @apply text-slate-400 w-20 flex-shrink-0;
}

.log-level {
  @apply w-16 flex-shrink-0 font-bold;
}

.log-message {
  @apply flex-1 whitespace-pre-wrap;
}

.log-info .log-level {
  @apply text-info-400;
}

.log-info .log-message {
  @apply text-slate-200;
}

.log-warning .log-level {
  @apply text-warning-400;
}

.log-warning .log-message {
  @apply text-warning-200;
}

.log-error .log-level {
  @apply text-danger-400;
}

.log-error .log-message {
  @apply text-danger-200;
}

.log-debug .log-level {
  @apply text-slate-400;
}

.log-debug .log-message {
  @apply text-slate-300;
}
</style>