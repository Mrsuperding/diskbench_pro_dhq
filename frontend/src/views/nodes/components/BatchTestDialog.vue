<template>
  <el-dialog
    v-model="visible"
    title="批量连接测试"
    width="600px"
    class="batch-test-dialog"
  >
    <div class="space-y-4">
      <!-- 测试进度 -->
      <div v-if="testing" class="mb-4">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm text-slate-300">测试进度</span>
          <span class="text-sm text-slate-400">{{ testProgress.current }} / {{ testProgress.total }}</span>
        </div>
        <el-progress
          :percentage="testProgress.percentage"
          :status="testProgress.status"
          :stroke-width="8"
        />
      </div>

      <!-- 节点列表 -->
      <div class="max-h-80 overflow-y-auto">
        <div
          v-for="node in nodes"
          :key="node.id"
          class="flex items-center justify-between p-3 rounded-lg bg-slate-700/30 mb-2"
        >
          <div class="flex items-center">
            <div :class="getStatusDotClass(node.status)" class="w-3 h-3 rounded-full mr-3"></div>
            <div>
              <div class="text-white font-medium">{{ node.node_name }}</div>
              <div class="text-sm text-slate-400">{{ node.host }}:{{ node.port }}</div>
            </div>
          </div>
          <div class="flex items-center space-x-2">
            <div v-if="testResults[node.id]" class="flex items-center">
              <CheckCircleIcon v-if="testResults[node.id].success" class="w-5 h-5 text-success-400" />
              <XCircleIcon v-else class="w-5 h-5 text-danger-400" />
              <span class="ml-1 text-sm" :class="testResults[node.id].success ? 'text-success-400' : 'text-danger-400'">
                {{ testResults[node.id].success ? '成功' : '失败' }}
              </span>
            </div>
            <div v-else-if="testing" class="flex items-center">
              <ArrowPathIcon class="w-5 h-5 text-primary-400 animate-spin" />
              <span class="ml-1 text-sm text-primary-400">测试中...</span>
            </div>
            <div v-else class="text-sm text-slate-400">待测试</div>
          </div>
        </div>
      </div>

      <!-- 测试结果统计 -->
      <div v-if="testComplete" class="border-t border-slate-700/50 pt-4">
        <div class="grid grid-cols-2 gap-4">
          <div class="text-center">
            <div class="text-2xl font-bold text-success-400">{{ testStats.success }}</div>
            <div class="text-sm text-slate-400">测试成功</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-danger-400">{{ testStats.failed }}</div>
            <div class="text-sm text-slate-400">测试失败</div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end space-x-3">
        <el-button @click="handleClose" :disabled="testing">
          {{ testComplete ? '关闭' : '取消' }}
        </el-button>
        <el-button
          v-if="!testing && !testComplete"
          type="primary"
          @click="startBatchTest"
        >
          开始测试
        </el-button>
        <el-button
          v-if="testComplete"
          type="primary"
          @click="handleSuccess"
        >
          确定
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useNodesStore } from '@stores/nodes'
import { ElMessage } from 'element-plus'
import {
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon
} from '@heroicons/vue/24/outline'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  nodes: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const nodesStore = useNodesStore()

// 状态
const testing = ref(false)
const testComplete = ref(false)
const testResults = ref({})
const testStats = ref({
  success: 0,
  failed: 0
})

// 测试进度
const testProgress = computed(() => {
  const total = props.nodes.length
  const current = Object.keys(testResults.value).length
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0
  const status = testStats.value.failed > 0 ? 'exception' : 'success'
  
  return {
    current,
    total,
    percentage,
    status
  }
})

// 对话框可见性
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
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

// 开始批量测试
const startBatchTest = async () => {
  if (props.nodes.length === 0) {
    ElMessage.warning('没有可测试的节点')
    return
  }

  testing.value = true
  testResults.value = {}
  testStats.value = { success: 0, failed: 0 }
  testComplete.value = false

  try {
    const results = await Promise.allSettled(
      props.nodes.map(async (node) => {
        try {
          const result = await nodesStore.testNodeConnection(node.id)
          return { nodeId: node.id, success: true, result }
        } catch (error) {
          return { nodeId: node.id, success: false, error: error.message }
        }
      })
    )

    results.forEach((result, index) => {
      const node = props.nodes[index]
      if (result.status === 'fulfilled') {
        testResults.value[node.id] = result.value
        if (result.value.success) {
          testStats.value.success++
        } else {
          testStats.value.failed++
        }
      } else {
        testResults.value[node.id] = {
          nodeId: node.id,
          success: false,
          error: result.reason?.message || '测试失败'
        }
        testStats.value.failed++
      }
    })

    testComplete.value = true
    ElMessage.success(`批量测试完成: ${testStats.value.success}个成功, ${testStats.value.failed}个失败`)
  } catch (error) {
    ElMessage.error('批量测试失败')
    console.error('Batch test error:', error)
  } finally {
    testing.value = false
  }
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
  resetState()
}

// 成功处理
const handleSuccess = () => {
  emit('success')
  handleClose()
}

// 重置状态
const resetState = () => {
  testing.value = false
  testComplete.value = false
  testResults.value = {}
  testStats.value = { success: 0, failed: 0 }
}
</script>

<style scoped>
.batch-test-dialog {
  @apply bg-slate-800/95 backdrop-blur-sm border-slate-600/50;
}

.batch-test-dialog :deep(.el-dialog__title) {
  @apply text-white;
}
</style>