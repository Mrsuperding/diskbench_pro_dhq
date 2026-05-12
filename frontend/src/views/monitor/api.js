import axios from 'axios'

export const fetchHistory = (hours = 24) =>
  axios.get('/api/monitor/history', { params: { hours } })

export const fetchRealTime = () =>
  axios.get('/api/monitor/real')

// 节点分区监控 API
export const partitionMonitorAPI = {
  // 开始分区监控
  startMonitor(data) {
    return axios.post('/api/monitor/node/partition/start', data)
  },

  // 停止分区监控
  stopMonitor(monitorId) {
    return axios.post('/api/monitor/node/partition/stop', { monitor_id: monitorId })
  },

  // 获取监控状态
  getMonitorStatus(monitorId) {
    return axios.get(`/api/monitor/node/partition/${monitorId}/status`)
  },

  // 列出所有活动监控
  listMonitors() {
    return axios.get('/api/monitor/node/partition/monitors')
  }
}
