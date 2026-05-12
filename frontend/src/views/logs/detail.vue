<template>
  <n-card>
    <template #header>
      <n-space justify="space-between">
        <span>日志详情</span>
        <n-button @click="$router.back()">返回</n-button>
      </n-space>
    </template>

    <n-descriptions bordered :column="1">
      <n-descriptions-item label="ID">{{ log.id }}</n-descriptions-item>
      <n-descriptions-item label="时间">{{ log.created_at }}</n-descriptions-item>
      <n-descriptions-item label="级别">
        <n-tag :type="levelColor">{{ log.level }}</n-tag>
      </n-descriptions-item>
      <n-descriptions-item label="模块">{{ log.module }}</n-descriptions-item>
      <n-descriptions-item label="消息">{{ log.message }}</n-descriptions-item>
      <n-descriptions-item label="堆栈" v-if="log.stack_trace">
        <n-code :code="log.stack_trace" language="log" />
      </n-descriptions-item>
    </n-descriptions>
  </n-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const log = ref({})

onMounted(async () => {
  const { data } = await axios.get(`/api/logs/${route.params.id}`)
  log.value = data
})

const levelColor = computed(() => {
  const lvl = log.value.level?.toLowerCase()
  return lvl === 'error' ? 'error' : lvl === 'warn' ? 'warning' : 'info'
})
</script>