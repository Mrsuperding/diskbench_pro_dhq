import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'

export const useMonitorStore = defineStore('monitor', {
  state: () => ({
    // 实时监控状态
    isRealtimeEnabled: false,
    refreshInterval: 5000,
    realtimeTimer: null,
    
    // 录制状态
    isRecording: false,
    recordingData: [],
    recordingStartTime: null,
    
    // 系统性能数据
    systemMetrics: {
      iops: 0,
      bandwidth: 0,
      latency: 0,
      cpu_usage: 0,
      memory_usage: 0,
      disk_usage: 0
    },
    
    // 历史数据
    historyData: [],
    
    // WebSocket连接
    wsConnection: null,
    
    // 告警配置
    alertRules: [],
    activeAlerts: []
  }),

  getters: {
    // 获取系统总览数据
    systemOverview: (state) => {
      return {
        total_iops: state.systemMetrics.iops,
        total_bandwidth: state.systemMetrics.bandwidth,
        avg_latency: state.systemMetrics.latency,
        cpu_usage: state.systemMetrics.cpu_usage,
        memory_usage: state.systemMetrics.memory_usage,
        disk_usage: state.systemMetrics.disk_usage
      }
    },
    
    // 获取录制时长
    recordingDuration: (state) => {
      if (!state.recordingStartTime) return 0
      return Date.now() - state.recordingStartTime
    },
    
    // 获取活跃告警数量
    activeAlertCount: (state) => {
      return state.activeAlerts.length
    }
  },

  actions: {
    // 开始实时监控
    startRealtimeMonitoring(interval = 5000) {
      this.isRealtimeEnabled = true
      this.refreshInterval = interval
      
      // 清除之前的定时器
      if (this.realtimeTimer) {
        clearInterval(this.realtimeTimer)
      }
      
      // 启动定时器
      this.realtimeTimer = setInterval(() => {
        this.fetchRealtimeData()
      }, interval)
      
      // 连接WebSocket
      this.connectWebSocket()
      
      ElMessage.success('实时监控已启动')
    },

    // 停止实时监控
    stopRealtimeMonitoring() {
      this.isRealtimeEnabled = false
      
      if (this.realtimeTimer) {
        clearInterval(this.realtimeTimer)
        this.realtimeTimer = null
      }
      
      // 断开WebSocket连接
      this.disconnectWebSocket()
      
      ElMessage.success('实时监控已停止')
    },

    // 设置刷新间隔
    setRefreshInterval(interval) {
      this.refreshInterval = interval
      
      if (this.isRealtimeEnabled) {
        this.startRealtimeMonitoring(interval)
      }
    },

    // 获取实时数据
    async fetchRealtimeData() {
      try {
        // 这里应该调用API获取实时性能数据
        // 模拟数据更新
        this.systemMetrics = {
          iops: Math.random() * 10000 + 5000,
          bandwidth: Math.random() * 1000000000 + 500000000, // ~500MB/s - 1.5GB/s
          latency: Math.random() * 5000 + 100, // 100μs - 5ms
          cpu_usage: Math.random() * 80 + 10, // 10% - 90%
          memory_usage: Math.random() * 90 + 10, // 10% - 100%
          disk_usage: Math.random() * 100 // 0% - 100%
        }
        
        // 如果正在录制，保存数据
        if (this.isRecording) {
          this.recordingData.push({
            timestamp: Date.now(),
            metrics: { ...this.systemMetrics }
          })
        }
        
        // 检查告警规则
        this.checkAlertRules()
        
      } catch (error) {
        console.error('Fetch realtime data error:', error)
      }
    },

    // 连接WebSocket
    connectWebSocket() {
      if (this.wsConnection) {
        return
      }

      const wsUrl = `ws://localhost:8000/api/monitor/ws`
      
      try {
        this.wsConnection = new WebSocket(wsUrl)
        
        this.wsConnection.onopen = () => {
          console.log('Monitor WebSocket connected')
        }
        
        this.wsConnection.onmessage = (event) => {
          const data = JSON.parse(event.data)
          this.handleWebSocketMessage(data)
        }
        
        this.wsConnection.onerror = (error) => {
          console.error('Monitor WebSocket error:', error)
        }
        
        this.wsConnection.onclose = () => {
          console.log('Monitor WebSocket disconnected')
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

    // 处理WebSocket消息
    handleWebSocketMessage(data) {
      if (data.type === 'metrics') {
        // 更新系统指标
        Object.assign(this.systemMetrics, data.metrics)
        
        // 如果正在录制，保存数据
        if (this.isRecording) {
          this.recordingData.push({
            timestamp: Date.now(),
            metrics: { ...data.metrics }
          })
        }
        
        // 检查告警规则
        this.checkAlertRules()
      } else if (data.type === 'alert') {
        // 处理告警消息
        this.handleAlertMessage(data.alert)
      }
    },

    // 开始录制
    startRecording() {
      this.isRecording = true
      this.recordingStartTime = Date.now()
      this.recordingData = []
      
      ElMessage.success('开始录制性能数据')
    },

    // 停止录制
    stopRecording() {
      this.isRecording = false
      this.recordingStartTime = null
      
      // 可以在这里添加保存录制数据的逻辑
      if (this.recordingData.length > 0) {
        this.saveRecordingData()
      }
      
      ElMessage.success('停止录制性能数据')
    },

    // 保存录制数据
    saveRecordingData() {
      const recordingInfo = {
        start_time: this.recordingStartTime,
        duration: this.recordingDuration,
        data_points: this.recordingData.length,
        data: this.recordingData
      }
      
      // 这里可以将数据保存到服务器或本地存储
      console.log('Recording data saved:', recordingInfo)
    },

    // 获取历史数据
    async fetchHistoryData(startTime, endTime) {
      try {
        // 这里应该调用API获取历史数据
        // 模拟历史数据
        const data = []
        const interval = 60000 // 1分钟间隔
        
        for (let time = startTime; time <= endTime; time += interval) {
          data.push({
            timestamp: time,
            metrics: {
              iops: Math.random() * 10000 + 5000,
              bandwidth: Math.random() * 1000000000 + 500000000,
              latency: Math.random() * 5000 + 100,
              cpu_usage: Math.random() * 80 + 10
            }
          })
        }
        
        this.historyData = data
        return data
      } catch (error) {
        console.error('Fetch history data error:', error)
        throw error
      }
    },

    // 添加告警规则
    addAlertRule(rule) {
      const newRule = {
        id: Date.now(),
        name: rule.name,
        metric: rule.metric,
        condition: rule.condition,
        threshold: rule.threshold,
        duration: rule.duration || 60,
        enabled: rule.enabled !== false,
        created_at: new Date().toISOString()
      }
      
      this.alertRules.push(newRule)
      ElMessage.success('告警规则添加成功')
    },

    // 删除告警规则
    removeAlertRule(ruleId) {
      const index = this.alertRules.findIndex(rule => rule.id === ruleId)
      if (index > -1) {
        this.alertRules.splice(index, 1)
        ElMessage.success('告警规则删除成功')
      }
    },

    // 检查告警规则
    checkAlertRules() {
      this.alertRules.forEach(rule => {
        if (!rule.enabled) return
        
        const currentValue = this.systemMetrics[rule.metric]
        let triggered = false
        
        switch (rule.condition) {
          case 'greater_than':
            triggered = currentValue > rule.threshold
            break
          case 'less_than':
            triggered = currentValue < rule.threshold
            break
          case 'equal_to':
            triggered = currentValue === rule.threshold
            break
          case 'not_equal_to':
            triggered = currentValue !== rule.threshold
            break
        }
        
        if (triggered) {
          this.triggerAlert(rule, currentValue)
        } else {
          this.clearAlert(rule.id)
        }
      })
    },

    // 触发告警
    triggerAlert(rule, currentValue) {
      const existingAlert = this.activeAlerts.find(alert => alert.rule_id === rule.id)
      
      if (existingAlert) {
        // 更新现有告警
        existingAlert.last_triggered = Date.now()
        existingAlert.current_value = currentValue
      } else {
        // 创建新告警
        const alert = {
          id: Date.now(),
          rule_id: rule.id,
          rule_name: rule.name,
          metric: rule.metric,
          condition: rule.condition,
          threshold: rule.threshold,
          current_value: currentValue,
          triggered_at: Date.now(),
          status: 'active'
        }
        
        this.activeAlerts.push(alert)
        
        // 发送通知
        this.sendAlertNotification(alert)
      }
    },

    // 清除告警
    clearAlert(ruleId) {
      const index = this.activeAlerts.findIndex(alert => alert.rule_id === ruleId)
      if (index > -1) {
        this.activeAlerts.splice(index, 1)
      }
    },

    // 发送告警通知
    sendAlertNotification(alert) {
      const message = `告警: ${alert.rule_name} - 当前值: ${alert.current_value}, 阈值: ${alert.threshold}`
      
      // 显示通知
      ElMessage.warning(message)
      
      // 这里可以添加其他通知方式，如邮件、短信等
      console.log('Alert notification:', message)
    },

    // 处理告警消息
    handleAlertMessage(alertData) {
      // 处理来自WebSocket的告警消息
      const alert = {
        id: alertData.id || Date.now(),
        rule_id: alertData.rule_id,
        rule_name: alertData.rule_name,
        metric: alertData.metric,
        condition: alertData.condition,
        threshold: alertData.threshold,
        current_value: alertData.current_value,
        triggered_at: alertData.triggered_at || Date.now(),
        status: alertData.status || 'active'
      }
      
      if (alertData.status === 'resolved') {
        this.clearAlert(alertData.rule_id)
      } else {
        this.activeAlerts.push(alert)
        this.sendAlertNotification(alert)
      }
    },

    // 获取实时数据
    getRealtimeData() {
      return {
        systemMetrics: this.systemMetrics,
        activeAlerts: this.activeAlerts,
        isRecording: this.isRecording,
        recordingDuration: this.recordingDuration
      }
    },

    // 清理数据
    cleanup() {
      if (this.realtimeTimer) {
        clearInterval(this.realtimeTimer)
        this.realtimeTimer = null
      }
      
      if (this.wsConnection) {
        this.wsConnection.close()
        this.wsConnection = null
      }
      
      this.isRealtimeEnabled = false
      this.isRecording = false
      this.recordingData = []
      this.activeAlerts = []
    }
  }
})