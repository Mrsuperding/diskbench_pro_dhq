<template>
  <el-dialog
    v-model="visible"
    title="创建测试任务"
    width="800px"
    class="task-dialog"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="120px"
      label-position="left"
    >
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- 基本信息 -->
        <div class="space-y-4">
          <h4 class="text-lg font-semibold text-white border-b border-slate-700/50 pb-2">基本信息</h4>
          
          <el-form-item label="任务名称" prop="name">
            <el-input
              v-model="formData.name"
              placeholder="请输入任务名称"
            />
          </el-form-item>

          <el-form-item label="测试用例" prop="case_id">
            <el-select
              v-model="formData.case_id"
              class="w-full"
              filterable
              placeholder="请选择测试用例"
            >
              <el-option
                v-for="case_ in availableCases"
                :key="case_.id"
                :label="case_.case_name"
                :value="case_.id"
              >
                <div class="flex items-center">
                  <span>{{ case_.case_name }}</span>
                  <el-tag v-if="case_.is_template" size="small" type="warning" class="ml-2">
                    模板
                  </el-tag>
                </div>
              </el-option>
            </el-select>
          </el-form-item>

          <el-form-item label="目标节点" prop="node_ids">
            <el-select
              v-model="formData.node_ids"
              class="w-full"
              multiple
              filterable
              placeholder="请选择目标节点"
            >
              <el-option
                v-for="node in availableNodes"
                :key="node.id"
                :label="node.node_name"
                :value="node.id"
              >
                <div class="flex items-center">
                  <div :class="getStatusDotClass(node.status)" class="w-2 h-2 rounded-full mr-2"></div>
                  <span>{{ node.node_name }}</span>
                  <span class="text-slate-400 ml-2">({{ node.host }})</span>
                </div>
              </el-option>
            </el-select>
          </el-form-item>

          <el-form-item label="测试路径" prop="test_path">
            <el-input
              v-model="formData.test_path"
              placeholder="例如: /tmp/testfile, /data/test"
            />
          </el-form-item>

          <el-form-item label="并发度" prop="concurrency">
            <el-input-number
              v-model="formData.concurrency"
              :min="1"
              :max="10"
              :step="1"
              class="w-full"
            />
          </el-form-item>
        </div>

        <!-- 执行配置 -->
        <div class="space-y-4">
          <h4 class="text-lg font-semibold text-white border-b border-slate-700/50 pb-2">执行配置</h4>

          <el-form-item label="优先级" prop="priority">
            <el-select v-model="formData.priority" class="w-full">
              <el-option label="低" :value="1" />
              <el-option label="中" :value="2" />
              <el-option label="高" :value="3" />
              <el-option label="紧急" :value="4" />
            </el-select>
          </el-form-item>

          <el-form-item label="超时时间" prop="timeout">
            <el-input-number
              v-model="formData.timeout"
              :min="60"
              :max="7200"
              :step="60"
              class="w-full"
            >
              <template #suffix>
                <span class="text-slate-400">秒</span>
              </template>
            </el-input-number>
          </el-form-item>

          <el-form-item label="重试次数" prop="retry_count">
            <el-input-number
              v-model="formData.retry_count"
              :min="0"
              :max="5"
              :step="1"
              class="w-full"
            />
          </el-form-item>

          <el-form-item label="自动清理" prop="auto_cleanup">
            <el-switch
              v-model="formData.auto_cleanup"
              active-text="是"
              inactive-text="否"
            />
          </el-form-item>

          <el-form-item label="邮件通知" prop="email_notification">
            <el-switch
              v-model="formData.email_notification"
              active-text="开启"
              inactive-text="关闭"
            />
          </el-form-item>
        </div>
      </div>

      <!-- 分区配置 -->
      <div v-if="formData.node_ids && formData.node_ids.length > 0" class="mt-6">
        <h4 class="text-lg font-semibold text-white mb-3">分区配置</h4>
        <PartitionSelector
          v-model="partitionMappings"
          :node-ids="formData.node_ids"
          @change="handlePartitionChange"
        />
      </div>

      <!-- 高级配置 -->
      <div class="mt-6">
        <el-collapse v-model="activeCollapse">
          <el-collapse-item title="高级配置" name="advanced">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
              <el-form-item label="环境变量" prop="environment_vars">
                <el-input
                  v-model="formData.environment_vars"
                  type="textarea"
                  :rows="3"
                  placeholder="KEY1=value1&#10;KEY2=value2"
                />
              </el-form-item>

              <el-form-item label="前置命令" prop="pre_commands">
                <el-input
                  v-model="formData.pre_commands"
                  type="textarea"
                  :rows="3"
                  placeholder="准备测试环境的命令&#10;每行一个命令"
                />
              </el-form-item>

              <el-form-item label="后置命令" prop="post_commands">
                <el-input
                  v-model="formData.post_commands"
                  type="textarea"
                  :rows="3"
                  placeholder="清理测试环境的命令&#10;每行一个命令"
                />
              </el-form-item>

              <el-form-item label="备注" prop="notes">
                <el-input
                  v-model="formData.notes"
                  type="textarea"
                  :rows="3"
                  placeholder="任务备注信息"
                />
              </el-form-item>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>

      <!-- 任务预览 -->
      <div class="mt-6" v-if="selectedCase && selectedNodes.length > 0">
        <h4 class="text-lg font-semibold text-white mb-3">任务预览</h4>
        <div class="bg-slate-700/30 p-4 rounded-lg">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span class="text-slate-400">用例:</span>
              <span class="text-white ml-2">{{ selectedCase.name }}</span>
            </div>
            <div>
              <span class="text-slate-400">节点:</span>
              <span class="text-white ml-2">{{ selectedNodes.map(n => n.node_name).join(', ') }}</span>
            </div>
            <div>
              <span class="text-slate-400">测试类型:</span>
              <span class="text-white ml-2">{{ getTestTypeText(selectedCase.test_type) }}</span>
            </div>
            <div>
              <span class="text-slate-400">并发度:</span>
              <span class="text-white ml-2">{{ formData.concurrency }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-form>

    <template #footer>
      <div class="flex justify-end space-x-3">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          @click="handleSubmit"
          :loading="submitLoading"
        >
          创建任务
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useTasksStore } from '@stores/tasks'
import { useCasesStore } from '@stores/cases'
import { useNodesStore } from '@stores/nodes'
import { ElMessage } from 'element-plus'
import PartitionSelector from './PartitionSelector.vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'success', 'close'])

const tasksStore = useTasksStore()
const casesStore = useCasesStore()
const nodesStore = useNodesStore()

const formRef = ref()
const submitLoading = ref(false)
const activeCollapse = ref([])

// 表单数据
const defaultFormData = {
  name: '',
  case_id: '',
  node_ids: [],
  test_path: '/tmp/testfile',
  concurrency: 1,
  priority: 2,
  timeout: 3600,
  retry_count: 0,
  auto_cleanup: true,
  email_notification: false,
  environment_vars: '',
  pre_commands: '',
  post_commands: '',
  notes: ''
}

const formData = ref({ ...defaultFormData })

// 分区配置映射
const partitionMappings = ref({})

// 表单规则
const formRules = {
  name: [
    { required: true, message: '请输入任务名称', trigger: 'blur' },
    { min: 3, max: 100, message: '任务名称长度在 3 到 100 个字符', trigger: 'blur' }
  ],
  case_id: [
    { required: true, message: '请选择测试用例', trigger: 'change' }
  ],
  node_ids: [
    { required: true, message: '请选择目标节点', trigger: 'change' },
    { type: 'array', min: 1, message: '至少选择一个节点', trigger: 'change' }
  ],
  test_path: [
    { required: true, message: '请输入测试路径', trigger: 'blur' },
    { pattern: /^\/.*/, message: '测试路径必须以 / 开头', trigger: 'blur' }
  ],
  concurrency: [
    { required: true, message: '请输入并发度', trigger: 'blur' },
    { type: 'number', min: 1, max: 10, message: '并发度范围为 1-10', trigger: 'blur' }
  ],
  timeout: [
    { required: true, message: '请输入超时时间', trigger: 'blur' },
    { type: 'number', min: 60, max: 7200, message: '超时时间范围为 60-7200 秒', trigger: 'blur' }
  ]
}

// 计算属性
const availableCases = computed(() => casesStore.regularCases)
const availableNodes = computed(() => nodesStore.nodes)

const selectedCase = computed(() => {
  if (!formData.value.case_id) return null
  return casesStore.getCaseById(formData.value.case_id)
})

const selectedNodes = computed(() => {
  if (!formData.value.node_ids || formData.value.node_ids.length === 0) return []
  return formData.value.node_ids.map(id => nodesStore.getCaseById(id)).filter(Boolean)
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

// 处理分区配置变化
const handlePartitionChange = (mappings) => {
  partitionMappings.value = mappings
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitLoading.value = true

    // 处理环境变量
    const environmentVars = {}
    if (formData.value.environment_vars) {
      formData.value.environment_vars.split('\n').forEach(line => {
        const [key, value] = line.split('=')
        if (key && value) {
          environmentVars[key.trim()] = value.trim()
        }
      })
    }

    // 转换为后端字段名
    const submitData = {
      task_name: formData.value.name,
      test_case_id: formData.value.case_id,
      node_ids: formData.value.node_ids,
      partition_mappings: partitionMappings.value,
      test_path: formData.value.test_path,
      concurrency: formData.value.concurrency,
      priority: formData.value.priority,
      timeout: formData.value.timeout,
      retry_count: formData.value.retry_count,
      auto_cleanup: formData.value.auto_cleanup,
      email_notification: formData.value.email_notification,
      environment_vars: environmentVars,
      pre_commands: formData.value.pre_commands ? formData.value.pre_commands.split('\n').filter(Boolean) : [],
      post_commands: formData.value.post_commands ? formData.value.post_commands.split('\n').filter(Boolean) : [],
      notes: formData.value.notes
    }

    await tasksStore.createTask(submitData)
    emit('success')
    visible.value = false
    resetForm()
  } catch (error) {
    console.error('Submit error:', error)
  } finally {
    submitLoading.value = false
  }
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
  resetForm()
  emit('close')
}

// 重置表单
const resetForm = () => {
  formData.value = { ...defaultFormData }
  if (formRef.value) {
    formRef.value.clearValidate()
  }
}

// 初始化
onMounted(() => {
  casesStore.fetchCases()
  nodesStore.fetchNodes()
})
</script>

<style scoped>
.task-dialog {
  @apply bg-slate-800/95 backdrop-blur-sm border-slate-600/50;
}

.task-dialog :deep(.el-dialog__title) {
  @apply text-white;
}

.task-dialog :deep(.el-form-item__label) {
  @apply text-slate-300;
}

.task-dialog :deep(.el-collapse-item__header) {
  @apply text-white bg-slate-700/30 border-slate-600/50;
}

.task-dialog :deep(.el-collapse-item__wrap) {
  @apply bg-slate-700/30 border-slate-600/50;
}
</style>