import api from './index'

export const tasksAPI = {
  // 获取任务列表
  getTasks(params = {}) {
    return api.get('/tasks/', { params })
  },

  // 获取任务详情
  getTask(taskId) {
    return api.get(`/tasks/${taskId}`)
  },

  // 创建任务
  createTask(data) {
    return api.post('/tasks/', data)
  },

  // 更新任务
  updateTask(taskId, data) {
    return api.put(`/tasks/${taskId}`, data)
  },

  // 删除任务
  deleteTask(taskId) {
    return api.delete(`/tasks/${taskId}`)
  },

  // 启动任务
  startTask(taskId) {
    return api.post(`/tasks/${taskId}/start`)
  },

  // 停止任务
  stopTask(taskId) {
    return api.post(`/tasks/${taskId}/stop`)
  },

  // 获取任务执行日志
  getTaskLogs(taskId) {
    return api.get(`/tasks/${taskId}/logs`)
  },

  // 获取任务性能数据
  getTaskMetrics(taskId) {
    return api.get(`/tasks/${taskId}/metrics`)
  },

  // 获取任务结果
  getTaskResults(taskId) {
    return api.get(`/tasks/${taskId}/results`)
  },

  // 获取任务的节点列表
  getTaskNodes(taskId) {
    return api.get(`/tasks/${taskId}/nodes`)
  },

  // 添加节点到任务
  addTaskNode(taskId, data) {
    return api.post(`/tasks/${taskId}/nodes`, data)
  },

  // 从任务移除节点
  removeTaskNode(taskId, nodeId) {
    return api.delete(`/tasks/${taskId}/nodes/${nodeId}`)
  },

  // 克隆任务
  cloneTask(taskId, data) {
    return api.post(`/tasks/${taskId}/clone`, data)
  },

  // 更新任务节点分区
  updateTaskNodePartitions(taskId, taskNodeId, data) {
    return api.put(`/tasks/${taskId}/nodes/${taskNodeId}`, data)
  },

  // 获取任务百分位延迟数据
  getTaskPercentiles(taskId) {
    return api.get(`/tasks/${taskId}/percentiles`)
  }
}