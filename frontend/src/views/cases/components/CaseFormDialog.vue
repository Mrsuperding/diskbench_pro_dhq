<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑用例' : '创建用例'"
    width="800px"
    class="case-dialog"
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
          
          <el-form-item label="用例名称" prop="name">
            <el-input
              v-model="formData.name"
              placeholder="请输入用例名称"
            />
          </el-form-item>

          <el-form-item label="测试类型" prop="test_type">
            <el-select v-model="formData.test_type" class="w-full">
              <el-option label="顺序读" value="sequential_read" />
              <el-option label="顺序写" value="sequential_write" />
              <el-option label="随机读" value="random_read" />
              <el-option label="随机写" value="random_write" />
              <el-option label="混合读写" value="mixed_rw" />
            </el-select>
          </el-form-item>

          <el-form-item label="描述" prop="description">
            <el-input
              v-model="formData.description"
              type="textarea"
              :rows="3"
              placeholder="请输入用例描述"
            />
          </el-form-item>

          <el-form-item label="设为模板" prop="is_template">
            <el-switch
              v-model="formData.is_template"
              active-text="是"
              inactive-text="否"
            />
          </el-form-item>
        </div>

        <!-- FIO参数 -->
        <div class="space-y-4">
          <h4 class="text-lg font-semibold text-white border-b border-slate-700/50 pb-2">FIO参数</h4>
          
          <el-form-item label="块大小" prop="block_size">
            <el-select v-model="formData.block_size" class="w-full">
              <el-option label="512B" value="512" />
              <el-option label="1K" value="1k" />
              <el-option label="2K" value="2k" />
              <el-option label="4K" value="4k" />
              <el-option label="8K" value="8k" />
              <el-option label="16K" value="16k" />
              <el-option label="32K" value="32k" />
              <el-option label="64K" value="64k" />
              <el-option label="128K" value="128k" />
              <el-option label="256K" value="256k" />
              <el-option label="512K" value="512k" />
              <el-option label="1M" value="1m" />
              <el-option label="2M" value="2m" />
              <el-option label="4M" value="4m" />
            </el-select>
          </el-form-item>

          <el-form-item label="队列深度" prop="iodepth">
            <el-input-number
              v-model="formData.iodepth"
              :min="1"
              :max="1024"
              :step="1"
              class="w-full"
            />
          </el-form-item>

          <el-form-item label="线程数" prop="numjobs">
            <el-input-number
              v-model="formData.numjobs"
              :min="1"
              :max="64"
              :step="1"
              class="w-full"
            />
          </el-form-item>

          <el-form-item label="测试时间" prop="runtime">
            <el-input-number
              v-model="formData.runtime"
              :min="1"
              :max="3600"
              :step="1"
              class="w-full"
            >
              <template #suffix>
                <span class="text-slate-400">秒</span>
              </template>
            </el-input-number>
          </el-form-item>

          <el-form-item label="文件大小" prop="filesize">
            <el-input
              v-model="formData.filesize"
              placeholder="例如: 1G, 512M, 100K"
            />
          </el-form-item>
        </div>
      </div>

      <!-- 高级参数 -->
      <div class="mt-6">
        <el-collapse v-model="activeCollapse">
          <el-collapse-item title="高级参数" name="advanced">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
              <el-form-item label="读写比例" prop="rwmixread">
                <el-input-number
                  v-model="formData.rwmixread"
                  :min="0"
                  :max="100"
                  :step="1"
                  class="w-full"
                >
                  <template #suffix>
                    <span class="text-slate-400">%</span>
                  </template>
                </el-input-number>
              </el-form-item>

              <el-form-item label="直接IO" prop="direct">
                <el-switch
                  v-model="formData.direct"
                  active-text="开启"
                  inactive-text="关闭"
                />
              </el-form-item>

              <el-form-item label="同步IO" prop="sync">
                <el-switch
                  v-model="formData.sync"
                  active-text="开启"
                  inactive-text="关闭"
                />
              </el-form-item>

              <el-form-item label="验证数据" prop="verify">
                <el-switch
                  v-model="formData.verify"
                  active-text="开启"
                  inactive-text="关闭"
                />
              </el-form-item>

              <el-form-item label="时间基准" prop="time_based">
                <el-switch
                  v-model="formData.time_based"
                  active-text="开启"
                  inactive-text="关闭"
                />
              </el-form-item>

              <el-form-item label="覆盖文件" prop="overwrite">
                <el-switch
                  v-model="formData.overwrite"
                  active-text="开启"
                  inactive-text="关闭"
                />
              </el-form-item>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>

      <!-- FIO命令预览 -->
      <div class="mt-6">
        <h4 class="text-lg font-semibold text-white mb-3">FIO命令预览</h4>
        <div class="code-block">
          <pre>{{ generatedCommand }}</pre>
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
          确定
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useCasesStore } from '@stores/cases'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  case: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'success', 'close'])

const casesStore = useCasesStore()
const formRef = ref()
const submitLoading = ref(false)
const activeCollapse = ref([])

// 表单数据
const defaultFormData = {
  name: '',
  description: '',
  test_type: 'sequential_read',
  block_size: '4k',
  iodepth: 1,
  numjobs: 1,
  runtime: 60,
  filesize: '1G',
  rwmixread: 50,
  direct: true,
  sync: false,
  verify: false,
  time_based: true,
  overwrite: true,
  is_template: false
}

const formData = ref({ ...defaultFormData })

// 表单规则
const formRules = {
  name: [
    { required: true, message: '请输入用例名称', trigger: 'blur' },
    { min: 3, max: 100, message: '用例名称长度在 3 到 100 个字符', trigger: 'blur' }
  ],
  test_type: [
    { required: true, message: '请选择测试类型', trigger: 'change' }
  ],
  block_size: [
    { required: true, message: '请选择块大小', trigger: 'change' }
  ],
  iodepth: [
    { required: true, message: '请输入队列深度', trigger: 'blur' },
    { type: 'number', min: 1, max: 1024, message: '队列深度范围为 1-1024', trigger: 'blur' }
  ],
  numjobs: [
    { required: true, message: '请输入线程数', trigger: 'blur' },
    { type: 'number', min: 1, max: 64, message: '线程数范围为 1-64', trigger: 'blur' }
  ],
  runtime: [
    { required: true, message: '请输入测试时间', trigger: 'blur' },
    { type: 'number', min: 1, max: 3600, message: '测试时间范围为 1-3600 秒', trigger: 'blur' }
  ],
  filesize: [
    { required: true, message: '请输入文件大小', trigger: 'blur' },
    { pattern: /^\d+[KMG]?$/, message: '请输入正确的文件大小格式，如 1G, 512M', trigger: 'blur' }
  ]
}

// 是否编辑模式
const isEdit = computed(() => !!props.case)

// 对话框可见性
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 生成FIO命令
const generatedCommand = computed(() => {
  const params = []
  
  // 基本参数
  params.push(`--name=${formData.value.name || 'test'}`)
  params.push(`--filename=testfile`)
  params.push(`--bs=${formData.value.block_size}`)
  params.push(`--iodepth=${formData.value.iodepth}`)
  params.push(`--numjobs=${formData.value.numjobs}`)
  params.push(`--runtime=${formData.value.runtime}`)
  params.push(`--size=${formData.value.filesize}`)
  
  // 测试类型
  const rwMap = {
    sequential_read: 'read',
    sequential_write: 'write',
    random_read: 'randread',
    random_write: 'randwrite',
    mixed_rw: 'randrw'
  }
  params.push(`--rw=${rwMap[formData.value.test_type] || 'read'}`)
  
  // 混合读写比例
  if (formData.value.test_type === 'mixed_rw') {
    params.push(`--rwmixread=${formData.value.rwmixread}`)
  }
  
  // 开关参数
  if (formData.value.direct) params.push('--direct=1')
  if (formData.value.sync) params.push('--sync=1')
  if (formData.value.verify) params.push('--verify=1')
  if (formData.value.time_based) params.push('--time_based=1')
  if (formData.value.overwrite) params.push('--overwrite=1')
  
  // 输出格式
  params.push('--output-format=json')
  params.push('--group_reporting')
  
  return `fio ${params.join(' ')}`
})

// 监听用例变化
watch(() => props.case, (newCase) => {
  if (newCase) {
    formData.value = {
      ...defaultFormData,
      ...newCase
    }
  } else {
    formData.value = { ...defaultFormData }
  }
}, { immediate: true })

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitLoading.value = true

    // 转换前端字段名为后端字段名
    const backendData = {
      case_name: formData.value.name,
      description: formData.value.description,
      test_type: formData.value.test_type,
      block_size: formData.value.block_size,
      iodepth: formData.value.iodepth,
      numjobs: formData.value.numjobs,
      runtime: formData.value.runtime,
      filesize: formData.value.filesize,
      rwmixread: formData.value.rwmixread,
      direct: formData.value.direct,
      sync: formData.value.sync,
      verify: formData.value.verify ? '1' : null,
      time_based: formData.value.time_based,
      overwrite: formData.value.overwrite,
      is_template: formData.value.is_template
    }

    if (isEdit.value) {
      await casesStore.updateCase(props.case.id, backendData)
    } else {
      await casesStore.createCase(backendData)
    }

    emit('success')
    visible.value = false
  } catch (error) {
    console.error('Submit error:', error)
  } finally {
    submitLoading.value = false
  }
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
  emit('close')
}
</script>

<style scoped>
.case-dialog {
  @apply bg-slate-800/95 backdrop-blur-sm border-slate-600/50;
}

.case-dialog :deep(.el-dialog__title) {
  @apply text-white;
}

.case-dialog :deep(.el-form-item__label) {
  @apply text-slate-300;
}

.case-dialog :deep(.el-collapse-item__header) {
  @apply text-white bg-slate-700/30 border-slate-600/50;
}

.case-dialog :deep(.el-collapse-item__wrap) {
  @apply bg-slate-700/30 border-slate-600/50;
}

.code-block {
  @apply bg-slate-900/50 text-slate-200 p-4 rounded-lg font-mono text-sm overflow-x-auto;
}
</style>