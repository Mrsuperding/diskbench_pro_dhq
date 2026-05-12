<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 p-4">
    <div class="w-full max-w-md bg-white rounded-lg shadow-md overflow-hidden">
      <div class="bg-primary p-6 text-center">
        <h1 class="text-2xl font-bold text-white">登录</h1>
      </div>
      <div class="p-6">
        <n-form ref="formRef" :model="form" :rules="rules" class="space-y-4">
          <n-form-item label="用户名" path="username" class="mb-2">
            <n-input
              v-model:value="form.username"
              placeholder="请输入用户名"
              class="w-full"
            />
          </n-form-item>
          <n-form-item label="密码" path="password" class="mb-2">
            <n-input
              v-model:value="form.password"
              type="password"
              placeholder="请输入密码"
              class="w-full"
            />
          </n-form-item>
          <n-form-item class="mt-6">
            <n-button
              type="primary"
              @click="handleSubmit"
              class="w-full"
              :loading="isLoading"
            >
              登录
            </n-button>
          </n-form-item>
        </n-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useWebSocketStore } from '@/stores/websocket'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

// 调试：添加生命周期钩子打印
onMounted(() => {
  console.log('Login组件已挂载')
})

const form = reactive({ username: '', password: '' })
const rules = {
  username: { required: true, message: '请输入用户名', trigger: 'blur' },
  password: { required: true, message: '请输入密码', trigger: 'blur' }
}
const formRef = ref()
const userStore = useUserStore()
const wsStore = useWebSocketStore()
const router = useRouter()
const route = useRoute()
const isLoading = ref(false)

function handleSubmit() {
  console.log('触发登录提交')
  formRef.value?.validate(async errors => {
    if (!errors) {
      try {
        isLoading.value = true
        console.log('登录请求参数:', form)
        await userStore.login(form)
        // 登录成功后初始化WebSocket连接
        wsStore.initialize()
        // 从redirect参数获取跳转路径，没有则跳转到home
        const redirect = route.query.redirect || '/home'
        router.push(decodeURIComponent(redirect))
        ElMessage.success('登录成功')
      } catch (error) {
        ElMessage.error('登录失败，请检查用户名和密码')
        console.error('Login error:', error)
      } finally {
        isLoading.value = false
      }
    } else {
      console.log('表单验证失败:', errors)
    }
  })
}

async function login() {
  const ok = await userStore.login(form)
  if (ok) router.push('/home')
}
</script>

<style scoped>
.bg-primary {
  background-color: #4285f4;
}
.shadow-md {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}
.rounded-lg {
  border-radius: 0.5rem;
}
.overflow-hidden {
  overflow: hidden;
}
.min-h-screen {
  min-height: 100vh;
}
.flex {
  display: flex;
}
.items-center {
  align-items: center;
}
.justify-center {
  justify-content: center;
}
.bg-gray-50 {
  background-color: #f9fafb;
}
.p-4 {
  padding: 1rem;
}
.w-full {
  width: 100%;
}
.max-w-md {
  max-width: 28rem;
}
.bg-white {
  background-color: #ffffff;
}
.p-6 {
  padding: 1.5rem;
}
.text-center {
  text-align: center;
}
.text-2xl {
  font-size: 1.5rem;
}
.font-bold {
  font-weight: 700;
}
.text-white {
  color: #ffffff;
}
.space-y-4 > :not([hidden]) ~ :not([hidden]) {
  --tw-space-y-reverse: 0;
  margin-top: calc(1rem * calc(1 - var(--tw-space-y-reverse)));
  margin-bottom: calc(1rem * var(--tw-space-y-reverse));
}
.mb-2 {
  margin-bottom: 0.5rem;
}
.mt-6 {
  margin-top: 1.5rem;
}
</style>