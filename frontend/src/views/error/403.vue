<template>
  <div class="min-h-screen flex items-center justify-center flex-col">
    <h1 class="text-6xl font-bold text-gray-800">403</h1>
    <p class="mt-4 text-xl text-gray-600">没有访问权限</p>
    <button @click="goBack" class="mt-6 px-6 py-2 bg-primary text-white rounded-lg">
      返回首页
    </button>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
const goBack = () => router.push('/home')
</script>