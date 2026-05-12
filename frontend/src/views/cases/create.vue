<template>
  <n-card title="新建测试用例">
    <n-form :model="form" :rules="rules" ref="formRef">
      <n-form-item label="用例名称" path="name">
        <n-input v-model:value="form.name" placeholder="例如：4K 随机写" />
      </n-form-item>
      <n-form-item label="描述" path="description">
        <n-input type="textarea" v-model:value="form.description" placeholder="测试步骤、预期结果..." />
      </n-form-item>
      <n-form-item>
        <n-space>
          <n-button type="primary" @click="submit">提交</n-button>
          <n-button @click="$router.back()">返回</n-button>
        </n-space>
      </n-form-item>
    </n-form>
  </n-card>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const formRef = ref()
const form = reactive({ name: '', description: '' })

const rules = {
  name: { required: true, message: '请输入用例名称', trigger: 'blur' },
  description: { required: true, message: '请输入描述', trigger: 'blur' }
}

async function submit() {
  try {
    await formRef.value.validate()
    await axios.post('/api/cases', form)
    window.$message.success('创建成功')
    router.push('/cases')
  } catch (e) {
    window.$message.error(e.response?.data?.detail || '创建失败')
  }
}
</script>