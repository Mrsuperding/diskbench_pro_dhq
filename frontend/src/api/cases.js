import api from './index'

export const casesAPI = {
  // 获取测试用例列表
  getCases(params = {}) {
    return api.get('/cases/', { params })
  },

  // 获取测试用例详情
  getCase(caseId) {
    return api.get(`/cases/${caseId}`)
  },

  // 创建测试用例
  createCase(data) {
    return api.post('/cases/', data)
  },

  // 更新测试用例
  updateCase(caseId, data) {
    return api.put(`/cases/${caseId}`, data)
  },

  // 删除测试用例
  deleteCase(caseId) {
    return api.delete(`/cases/${caseId}`)
  },

  // 获取FIO命令
  getFioCommand(caseId, filename) {
    return api.get(`/cases/${caseId}/fio-command`, { params: { filename } })
  },

  // 克隆测试用例
  cloneCase(caseId, data) {
    return api.post(`/cases/${caseId}/clone`, data)
  },

  // 获取用例模板
  getTemplates() {
    return api.get('/cases/templates/')
  },

  // 设置用例为模板
  setTemplate(caseId, isTemplate) {
    return api.post(`/cases/${caseId}/set-template`, { is_template: isTemplate })
  },

  // 搜索测试用例
  searchCases(query, params = {}) {
    return api.get('/cases/search/', { params: { query, ...params } })
  }
}