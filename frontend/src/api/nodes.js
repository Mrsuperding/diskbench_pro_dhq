import api from './index'

export const nodesAPI = {
  // 获取节点列表
  getNodes(params = {}) {
    return api.get('/nodes/', { params })
  },

  // 获取节点详情
  getNode(nodeId) {
    return api.get(`/nodes/${nodeId}`)
  },

  // 创建节点
  createNode(data) {
    return api.post('/nodes/', data)
  },

  // 更新节点
  updateNode(nodeId, data) {
    return api.put(`/nodes/${nodeId}`, data)
  },

  // 删除节点
  deleteNode(nodeId) {
    return api.delete(`/nodes/${nodeId}`)
  },

  // 测试节点连接
  testNodeConnection(nodeId) {
    return api.post(`/nodes/${nodeId}/test-connection`)
  },

  // 测试连接（不保存节点）
  testConnection(data) {
    return api.post('/nodes/test-connection', data)
  },

  // 更新节点状态
  updateNodeStatus(nodeId, status) {
    return api.put(`/nodes/${nodeId}/status`, { status })
  },

  // 获取节点分区列表
  getNodePartitions(nodeId) {
    return api.get(`/nodes/${nodeId}/partitions`)
  },

  // 创建节点分区
  createNodePartition(nodeId, data) {
    return api.post(`/nodes/${nodeId}/partitions`, data)
  },

  // 更新节点分区
  updateNodePartition(nodeId, partitionId, data) {
    return api.put(`/nodes/${nodeId}/partitions/${partitionId}`, data)
  },

  // 删除节点分区
  deleteNodePartition(nodeId, partitionId) {
    return api.delete(`/nodes/${nodeId}/partitions/${partitionId}`)
  }
}