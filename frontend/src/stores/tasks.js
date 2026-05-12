import { defineStore } from 'pinia'
import { tasksAPI } from '@api/tasks'
import { ElMessage } from 'element-plus'

export const useTasksStore = defineStore('tasks', {
  state: () => ({
    tasks: [],
    currentTask: null,
    taskLogs: [],
    taskMetrics: [],
    taskResults: [],
    loading: false,
    total: 0,
    queryParams: {
      page: 1,
      limit: 10,
      status_filter: '',
      search: ''
    },
    // WebSocket连接
    wsConnection: null,
    // 实时数据
    realtimeData: new Map()
  }),

  getters: {
    // 获取运行中的任务
    runningTasks: (state) => {
      return state.tasks.filter(task => task.status === 'running')
    },

    // 获取待执行的任务
    pendingTasks: (state) => {
      return state.tasks.filter(task => task.status === 'pending')
    },

    // 获取已完成的任务
    completedTasks: (state) => {
      return state.tasks.filter(task => task.status === 'completed')
    },

    // 获取失败的任务
    failedTasks: (state) => {
      return state.tasks.filter(task => task.status === 'failed')
    },

    // 根据ID获取任务
    getTaskById: (state) => (id) => {
      return state.tasks.find(task => task.id === id)
    },

    // 筛选任务
    filteredTasks: (state) => {
      let filtered = state.tasks

      if (state.queryParams.status_filter) {
        filtered = filtered.filter(task => task.status === state.queryParams.status_filter)
      }

      if (state.queryParams.search) {
        const search = state.queryParams.search.toLowerCase()
        filtered = filtered.filter(task =>
          task.task_name.toLowerCase().includes(search) ||
          (task.description && task.description.toLowerCase().includes(search))
        )
      }

      return filtered
    },

    // 获取任务的实时数据
    getRealtimeData: (state) => (taskId) => {
      return state.realtimeData.get(taskId) || null
    }
  },

  actions: {
    // 获取任务列表
    async fetchTasks(params = {}) {
      this.loading = true
      try {
        // 后端使用 skip/limit 分页
        const skip = ((this.queryParams.page || 1) - 1) * (this.queryParams.limit || 10)
        const response = await tasksAPI.getTasks({ ...this.queryParams, skip, limit: this.queryParams.limit || 10 })
        // 后端直接返回数组
        this.tasks = Array.isArray(response) ? response : []
        this.total = this.tasks.length
        return response
      } catch (error) {
        throw error
      } finally {
        this.loading = false
      }
    },

    // 获取任务详情
    async fetchTask(taskId) {
      this.loading = true
      try {
        const response = await tasksAPI.getTask(taskId)
        this.currentTask = response
        return response
      } catch (error) {
        throw error
      } finally {
        this.loading = false
      }
    },

    // 创建任务
    async createTask(taskData) {
      try {
        const response = await tasksAPI.createTask(taskData)
        ElMessage.success('任务创建成功')
        await this.fetchTasks()
        return response
      } catch (error) {
        throw error
      }
    },

    // 更新任务
    async updateTask(taskId, taskData) {
      try {
        const response = await tasksAPI.updateTask(taskId, taskData)
        ElMessage.success('任务更新成功')
        await this.fetchTasks()
        return response
      } catch (error) {
        throw error
      }
    },

    // 删除任务
    async deleteTask(taskId) {
      try {
        await tasksAPI.deleteTask(taskId)
        ElMessage.success('任务删除成功')
        await this.fetchTasks()
      } catch (error) {
        throw error
      }
    },

    // 启动任务
    async startTask(taskId) {
      try {
        await tasksAPI.startTask(taskId)
        ElMessage.success('任务启动成功')
        await this.fetchTasks()
        
        // 开始接收实时数据
        this.subscribeToRealtimeData(taskId)
      } catch (error) {
        throw error
      }
    },

    // 停止任务
    async stopTask(taskId) {
      try {
        await tasksAPI.stopTask(taskId)
        ElMessage.success('任务停止成功')
        await this.fetchTasks()
        
        // 停止接收实时数据
        this.unsubscribeFromRealtimeData(taskId)
      } catch (error) {
        throw error
      }
    },

    // 获取任务执行日志
    async fetchTaskLogs(taskId) {
      try {
        const response = await tasksAPI.getTaskLogs(taskId)
        this.taskLogs = response
        return response
      } catch (error) {
        throw error
      }
    },

    // 获取任务性能数据
    async fetchTaskMetrics(taskId) {
      try {
        const response = await tasksAPI.getTaskMetrics(taskId)
        this.taskMetrics = response
        return response
      } catch (error) {
        throw error
      }
    },

    // 获取任务结果
    async fetchTaskResults(taskId) {
      try {
        const response = await tasksAPI.getTaskResults(taskId)
        this.taskResults = response
        return response
      } catch (error) {
        throw error
      }
    },

    // 批量删除任务
    async batchDeleteTasks(taskIds) {
      try {
        await Promise.all(taskIds.map(id => tasksAPI.deleteTask(id)))
        ElMessage.success('批量删除成功')
        await this.fetchTasks()
      } catch (error) {
        throw error
      }
    },

    // 批量启动任务
    async batchStartTasks(taskIds) {
      try {
        const results = await Promise.allSettled(
          taskIds.map(id => this.startTask(id))
        )
        
        const successCount = results.filter(r => r.status === 'fulfilled').length
        const failCount = results.filter(r => r.status === 'rejected').length
        
        ElMessage.success(`批量启动完成: ${successCount}个成功, ${failCount}个失败`)
        await this.fetchTasks()
        return results
      } catch (error) {
        throw error
      }
    },

    // 批量停止任务
    async batchStopTasks(taskIds) {
      try {
        const results = await Promise.allSettled(
          taskIds.map(id => this.stopTask(id))
        )
        
        const successCount = results.filter(r => r.status === 'fulfilled').length
        const failCount = results.filter(r => r.status === 'rejected').length
        
        ElMessage.success(`批量停止完成: ${successCount}个成功, ${failCount}个失败`)
        await this.fetchTasks()
        return results
      } catch (error) {
        throw error
      }
    },

    // WebSocket连接管理
    connectWebSocket() {
      if (this.wsConnection) {
        return
      }

      // 这里应该连接到WebSocket服务器
      // 实际项目中需要根据后端API进行调整
      const wsUrl = `ws://localhost:8000/api/monitor/ws`
      
      try {
        this.wsConnection = new WebSocket(wsUrl)
        
        this.wsConnection.onopen = () => {
          console.log('WebSocket connected')
        }
        
        this.wsConnection.onmessage = (event) => {
          const data = JSON.parse(event.data)
          this.handleRealtimeData(data)
        }
        
        this.wsConnection.onerror = (error) => {
          console.error('WebSocket error:', error)
        }
        
        this.wsConnection.onclose = () => {
          console.log('WebSocket disconnected')
          this.wsConnection = null
        }
      } catch (error) {
        console.error('WebSocket connection failed:', error)
      }
    },

    // 断开WebSocket连接
    disconnectWebSocket() {
      if (this.wsConnection) {
        this.wsConnection.close()
        this.wsConnection = null
      }
    },

    // 处理实时数据
    handleRealtimeData(data) {
      if (data.taskId) {
        this.realtimeData.set(data.taskId, data)
      }
    },

    // 订阅任务实时数据
    subscribeToRealtimeData(taskId) {
      if (this.wsConnection && this.wsConnection.readyState === WebSocket.OPEN) {
        this.wsConnection.send(JSON.stringify({
          action: 'subscribe',
          taskId: taskId
        }))
      }
    },

    // 取消订阅任务实时数据
    unsubscribeFromRealtimeData(taskId) {
      if (this.wsConnection && this.wsConnection.readyState === WebSocket.OPEN) {
        this.wsConnection.send(JSON.stringify({
          action: 'unsubscribe',
          taskId: taskId
        }))
      }
    },

    // 设置查询参数
    setQueryParams(params) {
      this.queryParams = { ...this.queryParams, ...params }
    },

    // 重置查询参数
    resetQueryParams() {
      this.queryParams = {
        page: 1,
        limit: 10,
        status_filter: '',
        search: ''
      }
    }
  }
})