<template>
  <el-dialog
    v-model="visible"
    title="FIO命令预览"
    width="700px"
    class="command-dialog"
  >
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold text-white">生成的FIO命令</h3>
        <el-button
          type="primary"
          size="small"
          @click="copyCommand"
          :icon="ClipboardDocumentIcon"
        >
          复制命令
        </el-button>
      </div>
      
      <div class="code-block">
        <pre>{{ command }}</pre>
      </div>
      
      <div class="bg-slate-700/30 p-4 rounded-lg">
        <h4 class="text-white font-medium mb-2">参数说明</h4>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-slate-300">
          <div><code class="text-primary-400">--name</code>: 测试任务名称</div>
          <div><code class="text-primary-400">--filename</code>: 测试文件路径</div>
          <div><code class="text-primary-400">--bs</code>: 块大小</div>
          <div><code class="text-primary-400">--iodepth</code>: 队列深度</div>
          <div><code class="text-primary-400">--numjobs</code>: 并发线程数</div>
          <div><code class="text-primary-400">--runtime</code>: 测试运行时间</div>
          <div><code class="text-primary-400">--rw</code>: 读写模式</div>
          <div><code class="text-primary-400">--output-format</code>: 输出格式</div>
        </div>
      </div>
      
      <div class="bg-warning-900/20 border border-warning-700/50 p-4 rounded-lg">
        <h4 class="text-warning-300 font-medium mb-2 flex items-center">
          <ExclamationTriangleIcon class="w-4 h-4 mr-2" />
          使用说明
        </h4>
        <ul class="text-sm text-warning-200 space-y-1">
          <li>• 确保目标路径有足够的磁盘空间</li>
          <li>• 测试前请备份重要数据</li>
          <li>• 建议在测试专用环境中运行</li>
          <li>• 根据实际需求调整参数</li>
        </ul>
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
import { ClipboardDocumentIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  command: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'close'])

// 对话框可见性
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 复制命令
const copyCommand = async () => {
  try {
    await navigator.clipboard.writeText(props.command)
    ElMessage.success('命令已复制到剪贴板')
  } catch (error) {
    console.error('Copy failed:', error)
    ElMessage.error('复制失败')
  }
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
  emit('close')
}
</script>

<style scoped>
.command-dialog {
  @apply bg-slate-800/95 backdrop-blur-sm border-slate-600/50;
}

.command-dialog :deep(.el-dialog__title) {
  @apply text-white;
}

.code-block {
  @apply bg-slate-900/50 text-slate-200 p-4 rounded-lg font-mono text-sm overflow-x-auto;
}
</style>