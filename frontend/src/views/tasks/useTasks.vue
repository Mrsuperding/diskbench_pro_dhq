import { reactive } from 'vue'
import axios from 'axios'

export function useTasks() {
  const tasks = reactive([])
  const loading = ref(false)
  const pagination = reactive({ page: 1, pageSize: 10, itemCount: 0 })

  async function fetchTasks() {
    loading.value = true
    try {
      // 后端使用 skip/limit 分页
      const skip = (pagination.page - 1) * pagination.pageSize
      const { data } = await axios.get('/api/tasks', {
        params: { skip, limit: pagination.pageSize }
      })
      tasks.length = 0
      // 后端直接返回数组
      tasks.push(...data)
      // 需要单独获取总数（如果有的话）
    } finally {
      loading.value = false
    }
  }

  async function deleteTask(id) {
    await axios.delete(`/api/tasks/${id}`)
    window.$message.success('已删除')
    await fetchTasks()
  }

  return { tasks, loading, pagination, fetchTasks, deleteTask }
}