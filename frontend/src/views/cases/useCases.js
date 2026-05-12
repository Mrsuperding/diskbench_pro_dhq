import { ref, reactive } from 'vue'
import axios from 'axios'

export function useCases() {
  const cases = ref([])
  const loading = ref(false)
  const pagination = reactive({ page: 1, pageSize: 10, itemCount: 0 })

  async function fetchCases() {
    loading.value = true
    try {
      const { data } = await axios.get('/api/cases', {
        params: { page: pagination.page, size: pagination.pageSize }
      })
      cases.value = data.items
      pagination.itemCount = data.total
    } finally {
      loading.value = false
    }
  }

  async function deleteCase(id) {
    await axios.delete(`/api/cases/${id}`)
    window.$message.success('已删除')
    await fetchCases()
  }

  return { cases, loading, pagination, fetchCases, deleteCase }
}