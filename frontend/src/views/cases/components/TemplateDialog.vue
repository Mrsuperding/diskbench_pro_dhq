<template>
  <el-dialog
    v-model="visible"
    title="选择用例模板"
    width="800px"
    class="template-dialog"
  >
    <div class="space-y-4">
      <!-- 搜索 -->
      <div class="flex items-center space-x-3">
        <el-input
          v-model="searchQuery"
          placeholder="搜索模板名称或描述"
          class="flex-1"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <MagnifyingGlassIcon class="w-4 h-4" />
          </template>
        </el-input>
        <el-button @click="handleSearch" type="primary">
          搜索
        </el-button>
      </div>

      <!-- 模板列表 -->
      <div class="max-h-96 overflow-y-auto">
        <div
          v-if="templates.length > 0"
          class="grid grid-cols-1 md:grid-cols-2 gap-4"
        >
          <div
            v-for="template in templates"
            :key="template.id"
            class="card card-hover p-4 cursor-pointer"
            @click="handleSelect(template)"
          >
            <div class="flex items-start justify-between mb-3">
              <div class="flex items-center">
                <StarIcon class="w-5 h-5 text-warning-400 mr-2" />
                <h4 class="text-white font-medium">{{ template.name }}</h4>
              </div>
              <el-tag size="small" :type="getTestTypeTag(template.test_type)">
                {{ getTestTypeText(template.test_type) }}
              </el-tag>
            </div>
            
            <p v-if="template.description" class="text-sm text-slate-400 mb-3">
              {{ template.description }}
            </p>
            
            <div class="grid grid-cols-2 gap-2 text-xs text-slate-300">
              <div>块大小: {{ template.block_size }}</div>
              <div>队列深度: {{ template.iodepth }}</div>
              <div>线程数: {{ template.numjobs }}</div>
              <div>测试时间: {{ template.runtime }}s</div>
            </div>
            
            <div class="mt-3 pt-3 border-t border-slate-700/50">
              <div class="flex items-center justify-between">
                <span class="text-xs text-slate-400">创建于: {{ formatTime(template.created_at) }}</span>
                <el-button type="primary" size="small" @click.stop="handleSelect(template)">
                  使用模板
                </el-button>
              </div>
            </div>
          </div>
        </div>
        
        <div v-else class="text-center py-12">
          <StarIcon class="w-12 h-12 text-slate-600 mx-auto mb-2" />
          <p class="text-slate-400">暂无可用模板</p>
          <p class="text-sm text-slate-500 mt-1">请先创建一些用例并设为模板</p>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end">
        <el-button @click="handleClose">取消</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useCasesStore } from '@stores/cases'
import { StarIcon, MagnifyingGlassIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'select', 'close'])

const casesStore = useCasesStore()

// 状态
const searchQuery = ref('')
const loading = ref(false)

// 计算属性
const templates = computed(() => {
  if (!searchQuery.value) {
    return casesStore.templateCases
  }
  
  const search = searchQuery.value.toLowerCase()
  return casesStore.templateCases.filter(template =>
    template.name.toLowerCase().includes(search) ||
    (template.description && template.description.toLowerCase().includes(search))
  )
})

// 对话框可见性
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 获取测试类型标签
const getTestTypeTag = (testType) => {
  const tags = {
    sequential_read: 'primary',
    sequential_write: 'success',
    random_read: 'warning',
    random_write: 'danger',
    mixed_rw: 'info'
  }
  return tags[testType] || 'info'
}

// 获取测试类型文本
const getTestTypeText = (testType) => {
  const texts = {
    sequential_read: '顺序读',
    sequential_write: '顺序写',
    random_read: '随机读',
    random_write: '随机写',
    mixed_rw: '混合读写'
  }
  return texts[testType] || '未知'
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return '未知'
  return new Date(time).toLocaleDateString('zh-CN')
}

// 搜索处理
const handleSearch = () => {
  // 搜索已在计算属性中处理
}

// 选择模板
const handleSelect = (template) => {
  emit('select', template)
  handleClose()
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
  searchQuery.value = ''
  emit('close')
}

// 初始化
onMounted(() => {
  casesStore.fetchCases()
})
</script>

<style scoped>
.template-dialog {
  @apply bg-slate-800/95 backdrop-blur-sm border-slate-600/50;
}

.template-dialog :deep(.el-dialog__title) {
  @apply text-white;
}
</style>