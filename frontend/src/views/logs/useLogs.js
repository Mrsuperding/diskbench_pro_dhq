import { ref, reactive } from 'vue'
import axios from 'axios'

export function useLogs() {
  const logs = ref([])
  const loading = ref(false)
  const pagination = reactive({ page: 1, pageSize: 20, itemCount: 0 })

  async function fetchLogs() {
    loading.value = true
    try {
      const { data } = await axios.get('/api/logs', {
        params: { page: pagination.page, size: pagination.pageSize }
      })
      logs.value = data.items
      pagination.itemCount = data.total
    } finally {
      loading.value = false
    }
  }

  return { logs, loading, pagination, fetchLogs }
}