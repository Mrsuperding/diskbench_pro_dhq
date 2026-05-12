<template>
  <n-layout>
    <n-layout-header style="padding:10px">
      <n-space justify="space-between">
        <h3>DiskBench 控制台</h3>
        <n-button text @click="userStore.logout">退出</n-button>
      </n-space>
    </n-layout-header>
    <n-layout-content style="padding:20px">
      <n-alert type="info">欢迎 {{ userStore.username }}，登录成功！</n-alert>
    </n-layout-content>
  </n-layout>
</template>

<script setup>
import { useUserStore } from '@/stores/user'
const userStore = useUserStore()
</script>