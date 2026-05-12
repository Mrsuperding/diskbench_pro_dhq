<template>
  <el-dialog
    v-model="visible"
    :title="`任务结果 - ${task?.name || '未知任务'}`"
    width="1000px"
    class="results-dialog"
    @close="handleClose"
  >
    <div class="space-y-6">
      <!-- 结果概览 -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="card p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-slate-400">总IOPS</p>
              <p class="text-2xl font-bold text-white">{{ formatNumber(results.total_iops || 0) }}</p>
            </div>
            <div class="p-2 bg-primary-600/20 rounded-lg">
              <ChartBarIcon class="w-6 h-6 text-primary-400" />
            </div>
          </div>
        </div>

        <div class="card p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-slate-400">总带宽</p>
              <p class="text-2xl font-bold text-white">{{ formatBytes(results.total_bandwidth || 0) }}/s</p>
            </div>
            <div class="p-2 bg-success-600/20 rounded-lg">
              <ArrowDownTrayIcon class="w-6 h-6 text-success-400" />
            </div>
          </div>
        </div>

        <div class="card p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-slate-400">平均延迟</p>
              <p class="text-2xl font-bold text-white">{{ formatLatency(results.avg_latency || 0) }}</p>
            </div>
            <div class="p-2 bg-warning-600/20 rounded-lg">
              <ClockIcon class="w-6 h-6 text-warning-400" />
            </div>
          </div>
        </div>

        <div class="card p-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-slate-400">测试时长</p>
              <p class="text-2xl font-bold text-white">{{ formatDuration(results.test_duration || 0) }}</p>
            </div>
            <div class="p-2 bg-info-600/20 rounded-lg">
              <ClockIcon class="w-6 h-6 text-info-400" />
            </div>
          </div>
        </div>
      </div>

      <!-- 详细结果 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- 读性能 -->
        <div class="card p-6">
          <h4 class="text-white font-medium mb-4">读性能</h4>
          <div class="space-y-3">
            <div class="flex justify-between">
              <span class="text-slate-400">读IOPS</span>
              <span class="text-white">{{ formatNumber(results.read_iops || 0) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">读带宽</span>
              <span class="text-white">{{ formatBytes(results.read_bandwidth || 0) }}/s</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">读延迟</span>
              <span class="text-white">{{ formatLatency(results.read_latency || 0) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">读错误</span>
              <span class="text-white">{{ results.read_errors || 0 }}</span>
            </div>
          </div>
        </div>

        <!-- 写性能 -->
        <div class="card p-6">
          <h4 class="text-white font-medium mb-4">写性能</h4>
          <div class="space-y-3">
            <div class="flex justify-between">
              <span class="text-slate-400">写IOPS</span>
              <span class="text-white">{{ formatNumber(results.write_iops || 0) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">写带宽</span>
              <span class="text-white">{{ formatBytes(results.write_bandwidth || 0) }}/s</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">写延迟</span>
              <span class="text-white">{{ formatLatency(results.write_latency || 0) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">写错误</span>
              <span class="text-white">{{ results.write_errors || 0 }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 延迟分布 -->
      <div class="card p-6">
        <h4 class="text-white font-medium mb-4">延迟分布</h4>
        <div class="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div class="text-center">
            <div class="text-2xl font-bold text-white">{{ formatLatency(results.latency_50 || 0) }}</div>
            <div class="text-sm text-slate-400">P50</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-white">{{ formatLatency(results.latency_75 || 0) }}</div>
            <div class="text-sm text-slate-400">P75</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-white">{{ formatLatency(results.latency_95 || 0) }}</div>
            <div class="text-sm text-slate-400">P95</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-white">{{ formatLatency(results.latency_99 || 0) }}</div>
            <div class="text-sm text-slate-400">P99</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-white">{{ formatLatency(results.latency_max || 0) }}</div>
            <div class="text-sm text-slate-400">最大值</div>
          </div>
        </div>
      </div>

      <!-- 系统信息 -->
      <div class="card p-6">
        <h4 class="text-white font-medium mb-4">系统信息</h4>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-3">
            <div class="flex justify-between">
              <span class="text-slate-400">节点名称</span>
              <span class="text-white">{{ results.node_name || '未知' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">操作系统</span>
              <span class="text-white">{{ results.os_info || '未知' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">内核版本</span>
              <span class="text-white">{{ results.kernel_version || '未知' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">CPU信息</span>
              <span class="text-white">{{ results.cpu_info || '未知' }}</span>
            </div>
          </div>
          <div class="space-y-3">
            <div class="flex justify-between">
              <span class="text-slate-400">内存总量</span>
              <span class="text-white">{{ formatBytes(results.memory_total || 0) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">内存可用</span>
              <span class="text-white">{{ formatBytes(results.memory_available || 0) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">磁盘类型</span>
              <span class="text-white">{{ results.disk_type || '未知' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">文件系统</span>
              <span class="text-white">{{ results.filesystem || '未知' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="flex justify-end space-x-3">
        <el-button
          type="primary"
          @click="exportResults"
        >
          <ArrowDownTrayIcon class="w-4 h-4 mr-1" />
          导出结果
        </el-button>
        <el-button
          type="success"
          @click="shareResults"
        >
          <ShareIcon class="w-4 h-4 mr-1" />
          分享结果
        </el-button>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end">
        <el-button @click="handleClose">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ChartBarIcon,
  ArrowDownTrayIcon,
  ClockIcon,
  ShareIcon
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
  results: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'close'])

// 对话框可见性
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 格式化数字
const formatNumber = (num) => {
  return new Intl.NumberFormat('zh-CN').format(Math.round(num))
}

// 格式化字节
const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B'
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}

// 格式化延迟
const formatLatency = (microseconds) => {
  if (microseconds < 1000) {
    return Math.round(microseconds) + ' μs'
  } else if (microseconds < 1000000) {
    return Math.round(microseconds / 1000 * 100) / 100 + ' ms'
  } else {
    return Math.round(microseconds / 1000000 * 100) / 100 + ' s'
  }
}

// 格式化时长
const formatDuration = (seconds) => {
  if (!seconds) return '0秒'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`
  } else {
    return `${secs}s`
  }
}

// 导出结果
const exportResults = () => {
  const exportData = {
    task_info: {
      id: props.task?.id,
      name: props.task?.name,
      created_at: props.task?.created_at,
      completed_at: props.task?.completed_at
    },
    test_results: props.results
  }
  
  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `task-${props.task?.id}-results.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  
  ElMessage.success('结果导出成功')
}

// 分享结果
const shareResults = async () => {
  try {
    const shareText = `IO性能测试结果：\n任务：${props.task?.name}\n总IOPS：${formatNumber(props.results.total_iops || 0)}\n总带宽：${formatBytes(props.results.total_bandwidth || 0)}/s\n平均延迟：${formatLatency(props.results.avg_latency || 0)}`
    
    if (navigator.share) {
      await navigator.share({
        title: 'IO性能测试结果',
        text: shareText
      })
    } else {
      await navigator.clipboard.writeText(shareText)
      ElMessage.success('结果已复制到剪贴板')
    }
  } catch (error) {
    console.error('Share error:', error)
    ElMessage.error('分享失败')
  }
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
  emit('close')
}
</script>

<style scoped>
.results-dialog {
  @apply bg-slate-800/95 backdrop-blur-sm border-slate-600/50;
}

.results-dialog :deep(.el-dialog__title) {
  @apply text-white;
}
</style>