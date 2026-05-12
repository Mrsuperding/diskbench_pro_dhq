<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑节点' : '添加节点'"
    width="600px"
    class="node-dialog"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
      label-position="left"
    >
      <el-form-item label="节点名称" prop="node_name">
        <el-input
          v-model="formData.node_name"
          placeholder="请输入节点名称"
        />
      </el-form-item>

      <el-form-item label="主机地址" prop="host">
        <el-input
          v-model="formData.host"
          placeholder="请输入主机地址或IP"
        />
      </el-form-item>

      <el-form-item label="端口" prop="port">
        <el-input-number
          v-model="formData.port"
          :min="1"
          :max="65535"
          :step="1"
          class="w-full"
        />
      </el-form-item>

      <el-form-item label="认证方式" prop="login_type">
        <el-select v-model="formData.login_type" class="w-full">
          <el-option label="密码认证" value="password" />
          <el-option label="密钥认证" value="key" />
        </el-select>
      </el-form-item>

      <el-form-item label="用户名" prop="username">
        <el-input
          v-model="formData.username"
          placeholder="请输入SSH用户名"
        />
      </el-form-item>

      <el-form-item v-if="formData.login_type === 'password'" label="密码" prop="password">
        <el-input
          v-model="formData.password"
          type="password"
          placeholder="请输入SSH密码"
          show-password
        />
      </el-form-item>

      <el-form-item v-if="formData.login_type === 'key'" label="私钥" prop="private_key">
        <el-input
          v-model="formData.private_key"
          type="textarea"
          :rows="4"
          placeholder="请输入SSH私钥内容"
        />
      </el-form-item>

      <el-form-item label="系统类型" prop="os_type">
        <el-select v-model="formData.os_type" class="w-full">
          <el-option label="Linux" value="linux" />
          <el-option label="Windows" value="windows" />
          <el-option label="macOS" value="macos" />
          <el-option label="未知" value="unknown" />
        </el-select>
      </el-form-item>

      <el-form-item label="公开节点" prop="is_public">
        <el-switch
          v-model="formData.is_public"
          active-text="是"
          inactive-text="否"
        />
      </el-form-item>

      <el-form-item label="描述" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="请输入节点描述信息"
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
import { ref, computed, watch, nextTick } from 'vue'
import { useNodesStore } from '@stores/nodes'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  node: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'success', 'close'])

const nodesStore = useNodesStore()
const formRef = ref()
const submitLoading = ref(false)

// 表单数据
const defaultFormData = {
  node_name: '',
  host: '',
  port: 22,
  login_type: 'password',
  username: '',
  password: '',
  private_key: '',
  os_type: 'linux',
  is_public: false,
  description: ''
}

const formData = ref({ ...defaultFormData })

// 表单规则
const formRules = {
  node_name: [
    { required: true, message: '请输入节点名称', trigger: 'blur' },
    { min: 3, max: 50, message: '节点名称长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  host: [
    { required: true, message: '请输入主机地址', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9.-]+$/, message: '请输入正确的主机地址格式', trigger: 'blur' }
  ],
  port: [
    { required: true, message: '请输入端口号', trigger: 'blur' },
    { type: 'number', min: 1, max: 65535, message: '端口号范围为 1-65535', trigger: 'blur' }
  ],
  login_type: [
    { required: true, message: '请选择认证方式', trigger: 'change' }
  ],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 1, max: 50, message: '用户名长度在 1 到 50 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 1, max: 100, message: '密码长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  private_key: [
    { required: true, message: '请输入私钥', trigger: 'blur' }
  ],
  os_type: [
    { required: true, message: '请选择系统类型', trigger: 'change' }
  ]
}

// 是否编辑模式
const isEdit = computed(() => !!props.node)

// 对话框可见性
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 监听节点变化
watch(() => props.node, (newNode) => {
  if (newNode) {
    formData.value = {
      ...defaultFormData,
      ...newNode
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
    
    if (isEdit.value) {
      await nodesStore.updateNode(props.node.id, formData.value)
    } else {
      await nodesStore.createNode(formData.value)
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

// 监听认证方式变化，更新验证规则
watch(() => formData.value.login_type, (newType) => {
  if (newType === 'password') {
    formRules.private_key = []
    formRules.password = [
      { required: true, message: '请输入密码', trigger: 'blur' },
      { min: 1, max: 100, message: '密码长度在 1 到 100 个字符', trigger: 'blur' }
    ]
  } else {
    formRules.password = []
    formRules.private_key = [
      { required: true, message: '请输入私钥', trigger: 'blur' }
    ]
  }
  
  // 清除验证结果
  nextTick(() => {
    if (formRef.value) {
      formRef.value.clearValidate()
    }
  })
})
</script>

<style scoped>
.node-dialog {
  @apply bg-slate-800/95 backdrop-blur-sm border-slate-600/50;
}

.node-dialog :deep(.el-dialog__title) {
  @apply text-white;
}

.node-dialog :deep(.el-form-item__label) {
  @apply text-slate-300;
}
</style>