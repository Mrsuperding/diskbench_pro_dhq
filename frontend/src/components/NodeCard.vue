<template>
  <div class="bg-white rounded-lg shadow p-4 hover:shadow-lg transition-shadow">
    <div class="flex justify-between items-start mb-3">
      <div class="flex items-center space-x-3">
        <div
          class="w-3 h-3 rounded-full"
          :class="statusClass"
        ></div>
        <h3 class="text-lg font-medium text-gray-900">{{ node.name }}</h3>
      </div>
      <el-dropdown trigger="click">
        <el-button type="text" size="small">
          <el-icon><more-filled /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="handleEdit">
              <el-icon><edit /></el-icon>
              编辑
            </el-dropdown-item>
            <el-dropdown-item @click="handleDelete">
              <el-icon><delete /></el-icon>
              删除
            </el-dropdown-item>
            <el-dropdown-item @click="handleConnect">
              <el-icon><connection /></el-icon>
              连接测试
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <div class="space-y-2 text-sm text-gray-600">
      <div class="flex justify-between">
        <span>IP地址:</span>
        <span>{{ node.ip }}</span>
      </div>
      <div class="flex justify-between">
        <span>操作系统:</span>
        <span>{{ node.os }}</span>
      </div>
      <div class="flex justify-between">
        <span>CPU使用率:</span>
        <span>{{ node.metrics?.cpu }}%</span>
      </div>
      <div class="flex justify-between">
        <span>内存使用率:</span>
        <span>{{ node.metrics?.memory }}%</span>
      </div>
      <div class="flex justify-between">
        <span>磁盘数量:</span>
        <span>{{ node.diskCount || 0 }}个</span>
      </div>
    </div>

    <div class="mt-4 pt-3 border-t border-gray-100">
      <div class="flex justify-between items-center">
        <span class="text-xs text-gray-500">
          最后更新: {{ formatTime(node.lastUpdate) }}
        </span>
        <el-tag
          :type="statusTagType"
          size="small"
        >
          {{ statusText }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Edit, Delete, Connection, MoreFilled } from '@element-plus/icons-vue'

const props = defineProps({
  node: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['edit', 'delete', 'connect'])

const statusClass = computed(() => {
  const statusMap = {
    online: 'bg-green-500',
    offline: 'bg-red-500',
    testing: 'bg-yellow-500',
    unknown: 'bg-gray-500'
  }
  return statusMap[props.node.status] || statusMap.unknown
})

const statusTagType = computed(() => {
  const typeMap = {
    online: 'success',
    offline: 'danger',
    testing: 'warning',
    unknown: 'info'
  }
  return typeMap[props.node.status] || 'info'
})

const statusText = computed(() => {
  const textMap = {
    online: '在线',
    offline: '离线',
    testing: '测试中',
    unknown: '未知'
  }
  return textMap[props.node.status] || '未知'
})

const formatTime = (timestamp) => {
  if (!timestamp) return '从未'
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN')
}

const handleEdit = () => {
  emit('edit', props.node)
}

const handleDelete = () => {
  emit('delete', props.node)
}

const handleConnect = () => {
  emit('connect', props.node)
}
</script>