import { defineStore } from 'pinia'
import { nodesAPI } from '@api/nodes'
import { ElMessage } from 'element-plus'

export const useNodesStore = defineStore('nodes', {
  state: () => ({
    nodes: [],
    currentNode: null,
    partitions: [],
    loading: false,
    total: 0,
    queryParams: {
      page: 1,
      limit: 10,
      status_filter: '',
      search: ''
    }
  }),

  getters: {
    onlineNodes: (state) => {
      return state.nodes.filter(node => node.status === 'online')
    },
    
    offlineNodes: (state) => {
      return state.nodes.filter(node => node.status === 'offline')
    },
    
    filteredNodes: (state) => {
      let filtered = state.nodes
      
      if (state.queryParams.status_filter) {
        filtered = filtered.filter(node => node.status === state.queryParams.status_filter)
      }
      
      if (state.queryParams.search) {
        const search = state.queryParams.search.toLowerCase()
        filtered = filtered.filter(node => 
          node.node_name.toLowerCase().includes(search) ||
          node.host.toLowerCase().includes(search)
        )
      }
      
      return filtered
    }
  },

  actions: {
    // 获取节点列表
    async fetchNodes(params = {}) {
      this.loading = true
      try {
        const response = await nodesAPI.getNodes({ ...this.queryParams, ...params })
        this.nodes = response.items || response
        this.total = response.total || response.length
        return response
      } catch (error) {
        throw error
      } finally {
        this.loading = false
      }
    },

    // 获取节点详情
    async fetchNode(nodeId) {
      this.loading = true
      try {
        const response = await nodesAPI.getNode(nodeId)
        this.currentNode = response
        return response
      } catch (error) {
        throw error
      } finally {
        this.loading = false
      }
    },

    // 创建节点
    async createNode(nodeData) {
      try {
        const response = await nodesAPI.createNode(nodeData)
        ElMessage.success('节点创建成功')
        await this.fetchNodes()
        return response
      } catch (error) {
        throw error
      }
    },

    // 更新节点
    async updateNode(nodeId, nodeData) {
      try {
        const response = await nodesAPI.updateNode(nodeId, nodeData)
        ElMessage.success('节点更新成功')
        await this.fetchNodes()
        return response
      } catch (error) {
        throw error
      }
    },

    // 删除节点
    async deleteNode(nodeId) {
      try {
        await nodesAPI.deleteNode(nodeId)
        ElMessage.success('节点删除成功')
        await this.fetchNodes()
      } catch (error) {
        throw error
      }
    },

    // 测试节点连接
    async testNodeConnection(nodeId) {
      try {
        const response = await nodesAPI.testNodeConnection(nodeId)
        ElMessage.success('连接测试成功')
        return response
      } catch (error) {
        ElMessage.error('连接测试失败')
        throw error
      }
    },

    // 测试连接（不保存节点）
    async testConnection(connectionData) {
      try {
        const response = await nodesAPI.testConnection(connectionData)
        ElMessage.success('连接测试成功')
        return response
      } catch (error) {
        ElMessage.error('连接测试失败')
        throw error
      }
    },

    // 更新节点状态
    async updateNodeStatus(nodeId, status) {
      try {
        const response = await nodesAPI.updateNodeStatus(nodeId, status)
        ElMessage.success('节点状态更新成功')
        await this.fetchNodes()
        return response
      } catch (error) {
        throw error
      }
    },

    // 获取节点分区列表
    async fetchNodePartitions(nodeId) {
      try {
        const response = await nodesAPI.getNodePartitions(nodeId)
        this.partitions = response
        return response
      } catch (error) {
        throw error
      }
    },

    // 创建节点分区
    async createNodePartition(nodeId, partitionData) {
      try {
        const response = await nodesAPI.createNodePartition(nodeId, partitionData)
        ElMessage.success('分区创建成功')
        await this.fetchNodePartitions(nodeId)
        return response
      } catch (error) {
        throw error
      }
    },

    // 更新节点分区
    async updateNodePartition(nodeId, partitionId, partitionData) {
      try {
        const response = await nodesAPI.updateNodePartition(nodeId, partitionId, partitionData)
        ElMessage.success('分区更新成功')
        await this.fetchNodePartitions(nodeId)
        return response
      } catch (error) {
        throw error
      }
    },

    // 删除节点分区
    async deleteNodePartition(nodeId, partitionId) {
      try {
        await nodesAPI.deleteNodePartition(nodeId, partitionId)
        ElMessage.success('分区删除成功')
        await this.fetchNodePartitions(nodeId)
      } catch (error) {
        throw error
      }
    },

    // 批量删除节点
    async batchDeleteNodes(nodeIds) {
      try {
        await Promise.all(nodeIds.map(id => nodesAPI.deleteNode(id)))
        ElMessage.success('批量删除成功')
        await this.fetchNodes()
      } catch (error) {
        throw error
      }
    },

    // 批量测试节点连接
    async batchTestNodes(nodeIds) {
      try {
        const results = await Promise.allSettled(
          nodeIds.map(id => nodesAPI.testNodeConnection(id))
        )
        
        const successCount = results.filter(r => r.status === 'fulfilled').length
        const failCount = results.filter(r => r.status === 'rejected').length
        
        ElMessage.success(`测试完成: ${successCount}个成功, ${failCount}个失败`)
        await this.fetchNodes()
        return results
      } catch (error) {
        throw error
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