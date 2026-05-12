<template>
  <n-card title="系统日志">
    <n-space class="mb-4">
      <n-button type="primary" @click="refresh">刷新</n-button>
      <n-button @click="downloadLog" :loading="downLoading">下载当前页</n-button>
    </n-space>

    <n-data-table
      :columns="columns"
      :data="logs"
      :loading="loading"
      :pagination="pagination"
      @update:page="handlePage"
    />
  </n-card>
</template>

<script setup>
import { h, onMounted } from 'vue'
import { NButton, NSpace } from 'naive-ui'
import { useLogs } from './useLogs'
import axios from 'axios'

const { logs, loading, pagination, fetchLogs } = useLogs()
const downLoading = ref(false)

onMounted(fetchLogs)

const columns = [
  { title: 'ID', key: 'id', width: 80 },
  { title: '时间', key: 'created_at', width: 180 },
  { title: '级别', key: 'level', width: 100 },
  { title: '模块', key: 'module', width: 120 },
  { title: '消息', key: 'message', ellipsis: true },
  {
    title: '操作',
    key: 'actions',
    width: 100,
    render(row) {
      return h(NSpace, {}, () => [
        h(NButton, { size: 'small', onClick: () => $router.push(`/logs/detail/${row.id}`) }, '详情')
      ])
    }
  }
]

function handlePage(page) {
  pagination.page = page
  fetchLogs()
}

function refresh() {
  fetchLogs()
}

async function downloadLog() {
  downLoading.value = true
  try {
    const { data } = await axios.post('/api/logs/export', {
      page: pagination.page,
      size: pagination.pageSize
    }, { responseType: 'blob' })
    const blob = new Blob([data], { type: 'text/plain' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `logs_page_${pagination.page}.txt`
    a.click()
    window.URL.revokeObjectURL(url)
  } finally {
    downLoading.value = false
  }
}
</script>