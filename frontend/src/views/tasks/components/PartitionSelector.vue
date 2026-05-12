<template>
  <div class="partition-selector">
    <el-form-item label="分区配置" prop="partition_config">
      <div class="text-sm text-slate-400 mb-3">
        为每个选中的节点选择测试分区，并设置测试容量限制
      </div>

      <div v-if="loading" class="flex items-center justify-center py-8">
        <el-icon class="is-loading text-2xl text-primary-500">
          <Loading />
        </el-icon>
        <span class="ml-2">加载分区信息...</span>
      </div>

      <div v-else-if="nodePartitions.length === 0" class="text-slate-400 py-4">
        请先选择节点
      </div>

      <div v-else class="space-y-4">
        <div
          v-for="nodeInfo in nodePartitions"
          :key="nodeInfo.node_id"
          class="bg-slate-700/30 p-4 rounded-lg border border-slate-600/50"
        >
          <div class="flex items-center mb-3">
            <div :class="getStatusDotClass(nodeInfo.status)" class="w-2 h-2 rounded-full mr-2"></div>
            <span class="font-medium text-white">{{ nodeInfo.node_name }}</span>
            <span class="text-slate-400 ml-2">({{ nodeInfo.host }})</span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <el-form-item label="选择分区" class="mb-0">
              <el-select
                v-model="nodeInfo.selected_partition_id"
                class="w-full"
                filterable
                placeholder="选择分区"
                @change="handlePartitionChange(nodeInfo)"
              >
                <el-option
                  v-for="partition in nodeInfo.partitions"
                  :key="partition.id"
                  :label="partition.partition_name"
                  :value="partition.id"
                >
                  <div class="flex items-center justify-between w-full">
                    <span>{{ partition.partition_name }}</span>
                    <span class="text-slate-400 text-xs ml-2">
                      {{ partition.mount_point }} | {{ formatSize(partition.total_size) }}
                    </span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>

            <el-form-item label="容量限制(MB)" class="mb-0">
              <el-input-number
                v-model="nodeInfo.capacity_limit"
                :min="0"
                :max="nodeInfo.selected_partition?.total_size || 0"
                :step="100"
                class="w-full"
                placeholder="0表示无限制"
              />
            </el-form-item>
          </div>

          <div v-if="nodeInfo.selected_partition" class="mt-2 text-xs text-slate-400">
            <span>挂载点: {{ nodeInfo.selected_partition.mount_point }}</span>
            <span class="ml-3">文件系统: {{ nodeInfo.selected_partition.filesystem }}</span>
            <span class="ml-3">
              可用空间: {{ formatSize(nodeInfo.selected_partition.available_size) }} /
              {{ formatSize(nodeInfo.selected_partition.total_size) }}
            </span>
          </div>
        </div>
      </div>
    </el-form-item>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { nodesAPI } from '@api/nodes'

const props = defineProps({
  nodeIds: {
    type: Array,
    default: () => []
  },
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const loading = ref(false)
const nodePartitions = ref([])

// 计算属性：生成分区映射
const partitionMappings = computed(() => {
  const mappings = {}
  for (const np of nodePartitions.value) {
    if (np.selected_partition_id) {
      mappings[np.node_id] = {
        partition_id: np.selected_partition_id,
        capacity_limit: np.capacity_limit || 0
      }
    }
  }
  return mappings
})

// 获取状态点样式
const getStatusDotClass = (status) => {
  const classes = {
    online: 'bg-success-500',
    offline: 'bg-danger-500',
    unknown: 'bg-slate-500'
  }
  return classes[status] || 'bg-slate-500'
}

// 格式化大小
const formatSize = (sizeMB) => {
  if (!sizeMB) return '未知'
  if (sizeMB >= 1024) {
    return `${(sizeMB / 1024).toFixed(1)} GB`
  }
  return `${sizeMB} MB`
}

// 加载节点分区信息
const loadNodePartitions = async () => {
  if (!props.nodeIds || props.nodeIds.length === 0) {
    nodePartitions.value = []
    return
  }

  loading.value = true
  try {
    const response = await nodesAPI.getNodes({ limit: 100 })
    const nodes = response.items || response || []

    // 为每个选中的节点加载分区
    const promises = props.nodeIds.map(async (nodeId) => {
      const node = nodes.find(n => n.id === nodeId)
      if (!node) return null

      // 获取节点详情以获取分区信息
      try {
        const nodeDetail = await nodesAPI.getNode(nodeId)
        return {
          node_id: node.id,
          node_name: node.node_name,
          host: node.host,
          status: node.status,
          partitions: nodeDetail.partitions || [],
          selected_partition_id: nodeDetail.partitions?.length > 0 ? nodeDetail.partitions[0].id : null,
          capacity_limit: 0,
          selected_partition: nodeDetail.partitions?.length > 0 ? nodeDetail.partitions[0] : null
        }
      } catch (e) {
        // 如果获取详情失败，尝试使用列表中的基本信息
        return {
          node_id: node.id,
          node_name: node.node_name,
          host: node.host,
          status: node.status,
          partitions: node.partitions || [],
          selected_partition_id: node.partitions?.length > 0 ? node.partitions[0].id : null,
          capacity_limit: 0,
          selected_partition: node.partitions?.length > 0 ? node.partitions[0] : null
        }
      }
    })

    const results = await Promise.all(promises)
    nodePartitions.value = results.filter(Boolean)
  } catch (error) {
    console.error('Failed to load node partitions:', error)
    ElMessage.error('加载节点分区信息失败')
  } finally {
    loading.value = false
  }
}

// 处理分区选择变化
const handlePartitionChange = (nodeInfo) => {
  nodeInfo.selected_partition = nodeInfo.partitions.find(
    p => p.id === nodeInfo.selected_partition_id
  )
  emitChange()
}

// 发出变更事件
const emitChange = () => {
  emit('update:modelValue', partitionMappings.value)
  emit('change', partitionMappings.value)
}

// 监听节点变化
watch(() => props.nodeIds, async (newNodeIds) => {
  await loadNodePartitions()
}, { immediate: true })

// 初始化
onMounted(() => {
  if (props.nodeIds.length > 0) {
    loadNodePartitions()
  }
})
</script>

<style scoped>
.partition-selector :deep(.el-form-item__label) {
  color: var(--el-text-color-regular);
}

.partition-selector :deep(.el-input-number) {
  width: 100%;
}
</style>