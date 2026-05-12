<template>
  <n-card title="编辑测试用例">
    <n-form :model="form" :rules="rules" ref="formRef">
      <n-form-item label="用例名称" path="name">
        <n-input v-model:value="form.name" />
      </n-form-item>
      <n-form-item label="描述" path="description">
        <n-input type="textarea" v-model:value="form.description" />
      </n-form-item>
      <n-form-item>
        <n-space>
          <n-button type="primary" @click="submit">保存</n-button>
          <n-button @click="$router.back()">返回</n-button>
        </n-space>
      </n-form-item>
    </n-form>
  </n-card>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const formRef = ref()
const form = reactive({ name: '', description: '' })

const rules = {
  name: { required: true, message: '请输入用例名称', trigger: 'blur' },
  description: { required: true, message: '请输入描述', trigger: 'blur' }
}

onMounted(async () => {
  const { data } = await axios.get(`/api/cases/${route.params.id}`)
  Object.assign(form, data)
})

async function submit() {
  try {
    await formRef.value.validate()
    await axios.put(`/api/cases/${route.params.id}`, form)
    window.$message.success('更新成功')
    router.push('/cases')
  } catch (e) {
    window.$message.error(e.response?.data?.detail || '更新失败')
  }
}
</script>