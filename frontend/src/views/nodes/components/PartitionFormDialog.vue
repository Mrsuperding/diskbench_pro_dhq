<template>
  <el-dialog
    v-model="visible"
    title="添加分区"
    width="500px"
    class="partition-dialog"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
      label-position="left"
    >
      <el-form-item label="挂载点" prop="mount_point">
        <el-input
          v-model="formData.mount_point"
          placeholder="例如: /data, /mnt/storage"
        />
      </el-form-item>

      <el-form-item label="文件系统" prop="filesystem">
        <el-select v-model="formData.filesystem" class="w-full">
          <el-option label="ext4" value="ext4" />
          <el-option label="ext3" value="ext3" />
          <el-option label="xfs" value="xfs" />
          <el-option label="btrfs" value="btrfs" />
          <el-option label="ntfs" value="ntfs" />
          <el-option label="fat32" value="fat32" />
          <el-option label="其他" value="other" />
        </el-select>
      </el-form-item>

      <el-form-item label="总大小(GB)" prop="total_size">
        <el-input-number
          v-model="formData.total_size"
          :min="1"
          :max="1000000"
          :step="1"
          class="w-full"
        />
      </el-form-item>

      <el-form-item label="可用空间(GB)" prop="available_size">
        <el-input-number
          v-model="formData.available_size"
          :min="0"
          :max="formData.total_size"
          :step="1"
          class="w-full"
        />
      </el-form-item>

      <el-form-item label="描述" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="请输入分区描述信息"
        />
      </el-form-item>
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
import { ref, computed, watch } from 'vue'
import { useNodesStore } from '@stores/nodes'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  nodeId: {
    type: [String, Number],
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'success', 'close'])

const nodesStore = useNodesStore()
const formRef = ref()
const submitLoading = ref(false)

// 表单数据
const defaultFormData = {
  mount_point: '',
  filesystem: 'ext4',
  total_size: 100,
  available_size: 100,
  description: ''
}

const formData = ref({ ...defaultFormData })

// 表单规则
const formRules = {
  mount_point: [
    { required: true, message: '请输入挂载点', trigger: 'blur' },
    { pattern: /^\/.*/, message: '挂载点必须以 / 开头', trigger: 'blur' },
    { min: 2, max: 100, message: '挂载点长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  filesystem: [
    { required: true, message: '请选择文件系统类型', trigger: 'change' }
  ],
  total_size: [
    { required: true, message: '请输入总大小', trigger: 'blur' },
    { type: 'number', min: 1, max: 1000000, message: '总大小范围为 1-1000000 GB', trigger: 'blur' }
  ],
  available_size: [
    { required: true, message: '请输入可用空间', trigger: 'blur' },
    { type: 'number', min: 0, max: 1000000, message: '可用空间不能为负数', trigger: 'blur' }
  ]
}

// 对话框可见性
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 监听总大小变化，自动调整可用空间
watch(() => formData.value.total_size, (newTotal) => {
  if (formData.value.available_size > newTotal) {
    formData.value.available_size = newTotal
  }
})

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitLoading.value = true
    
    // 转换为字节
    const submitData = {
      ...formData.value,
      total_size: formData.value.total_size * 1024 * 1024 * 1024,
      available_size: formData.value.available_size * 1024 * 1024 * 1024
    }
    
    await nodesStore.createNodePartition(props.nodeId, submitData)
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
</script>

<style scoped>
.partition-dialog {
  @apply bg-slate-800/95 backdrop-blur-sm border-slate-600/50;
}

.partition-dialog :deep(.el-dialog__title) {
  @apply text-white;
}

.partition-dialog :deep(.el-form-item__label) {
  @apply text-slate-300;
}
</style>