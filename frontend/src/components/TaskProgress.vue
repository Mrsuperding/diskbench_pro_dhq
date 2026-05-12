<template>
  <div class="bg-white rounded-lg shadow p-4">
    <div class="flex justify-between items-center mb-3">
      <h4 class="text-lg font-medium text-gray-900">{{ task.name }}</h4>
      <el-tag :type="getStatusType(task.status)" size="small">
        {{ getStatusText(task.status) }}
      </el-tag>
    </div>

    <div class="mb-4">
      <div class="flex justify-between text-sm mb-1">
        <span class="text-gray-600">执行进度</span>
        <span class="font-medium">{{ task.progress }}%</span>
      </div>
      <el-progress
        :percentage="task.progress"
        :color="getProgressColor(task.status)"
        :stroke-width="8"
        :show-text="false"
      />
    </div>

    <div class="grid grid-cols-2 gap-4 mb-4 text-sm">
      <div>
        <span class="text-gray-600">用例: </span>
        <span class="font-medium">{{ task.caseName }}</span>
      </div>
      <div>
        <span class="text-gray-600">节点: </span>
        <span class="font-medium">{{ task.nodeCount }}个</span>
      </div>
      <div>
        <span class="text-gray-600">开始时间: </span>
        <span class="font-medium">{{ formatTime(task.startTime) }}</span>
      </div>
      <div>
        <span class="text-gray-600">预计完成: </span>
        <span class="font-medium">{{ formatTime(task.estimatedEnd) }}</span>
      </div>
    </div>

    <div class="flex justify-between items-center">
      <span class="text-xs text-gray-500">
        已运行: {{ formatDuration(task.elapsed) }}
      </span>
      <div class="flex space-x-2">
        <el-button
          v-if="task.status === 'running'"
          type="warning"
          link
          size="small"
          @click="$emit('pause', task)"
        >
          暂停
        </el-button>
        <el-button
          type="primary"
          link
          size="small"
          @click="$emit('view', task)"
        >
          查看详情
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { formatTime, formatDuration } from '@/utils/format'

defineProps({
  task: {
    type: Object,
    required: true
  }
})

defineEmits(['pause', 'view'])

const getStatusType = (status) => {
  const types = {
    pending: 'info',
    running: 'primary',
    completed: 'success',
    failed: 'danger',
    paused: 'warning'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    paused: '已暂停'
  }
  return texts[status] || status
}

const getProgressColor = (status) => {
  const colors = {
    pending: '#909399',
    running: '#409EFF',
    completed: '#67C23A',
    failed: '#F56C6C',
    paused: '#E6A23C'
  }
  return colors[status] || '#909399'
}
</script>