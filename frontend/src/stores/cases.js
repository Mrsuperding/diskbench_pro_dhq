import { defineStore } from 'pinia'
import { casesAPI } from '@api/cases'
import { ElMessage } from 'element-plus'

export const useCasesStore = defineStore('cases', {
  state: () => ({
    cases: [],
    currentCase: null,
    templates: [],
    loading: false,
    total: 0,
    queryParams: {
      page: 1,
      limit: 10,
      template_only: false,
      search: ''
    }
  }),

  getters: {
    // 获取所有用例（不包括模板）
    regularCases: (state) => {
      return state.cases.filter(case_ => !case_.is_template)
    },

    // 获取模板用例
    templateCases: (state) => {
      return state.cases.filter(case_ => case_.is_template)
    },

    // 根据ID获取用例
    getCaseById: (state) => (id) => {
      return state.cases.find(case_ => case_.id === id)
    },

    // 筛选用例
    filteredCases: (state) => {
      let filtered = state.cases

      if (state.queryParams.search) {
        const search = state.queryParams.search.toLowerCase()
        filtered = filtered.filter(case_ =>
          case_.name.toLowerCase().includes(search) ||
          case_.description.toLowerCase().includes(search)
        )
      }

      if (state.queryParams.template_only) {
        filtered = filtered.filter(case_ => case_.is_template)
      }

      return filtered
    }
  },

  actions: {
    // 获取测试用例列表
    async fetchCases(params = {}) {
      this.loading = true
      try {
        const response = await casesAPI.getCases({ ...this.queryParams, ...params })
        this.cases = response.items || response
        this.total = response.total || response.length
        return response
      } catch (error) {
        throw error
      } finally {
        this.loading = false
      }
    },

    // 获取测试用例详情
    async fetchCase(caseId) {
      this.loading = true
      try {
        const response = await casesAPI.getCase(caseId)
        this.currentCase = response
        return response
      } catch (error) {
        throw error
      } finally {
        this.loading = false
      }
    },

    // 创建测试用例
    async createCase(caseData) {
      try {
        const response = await casesAPI.createCase(caseData)
        ElMessage.success('测试用例创建成功')
        await this.fetchCases()
        return response
      } catch (error) {
        throw error
      }
    },

    // 更新测试用例
    async updateCase(caseId, caseData) {
      try {
        const response = await casesAPI.updateCase(caseId, caseData)
        ElMessage.success('测试用例更新成功')
        await this.fetchCases()
        return response
      } catch (error) {
        throw error
      }
    },

    // 删除测试用例
    async deleteCase(caseId) {
      try {
        await casesAPI.deleteCase(caseId)
        ElMessage.success('测试用例删除成功')
        await this.fetchCases()
      } catch (error) {
        throw error
      }
    },

    // 获取FIO命令
    async getFioCommand(caseId, filename = 'testfile') {
      try {
        return await casesAPI.getFioCommand(caseId, filename)
      } catch (error) {
        throw error
      }
    },

    // 克隆测试用例
    async cloneCase(caseId, newName) {
      try {
        const response = await casesAPI.cloneCase(caseId, { new_name: newName })
        ElMessage.success('测试用例克隆成功')
        await this.fetchCases()
        return response
      } catch (error) {
        throw error
      }
    },

    // 获取用例模板
    async fetchTemplates() {
      try {
        const response = await casesAPI.getTemplates()
        this.templates = response
        return response
      } catch (error) {
        throw error
      }
    },

    // 设置用例为模板
    async setTemplate(caseId, isTemplate) {
      try {
        const response = await casesAPI.setTemplate(caseId, isTemplate)
        const message = isTemplate ? '已设置为模板' : '已取消模板'
        ElMessage.success(message)
        await this.fetchCases()
        return response
      } catch (error) {
        throw error
      }
    },

    // 搜索测试用例
    async searchCases(query, params = {}) {
      try {
        return await casesAPI.searchCases(query, params)
      } catch (error) {
        throw error
      }
    },

    // 批量删除用例
    async batchDeleteCases(caseIds) {
      try {
        await Promise.all(caseIds.map(id => casesAPI.deleteCase(id)))
        ElMessage.success('批量删除成功')
        await this.fetchCases()
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
        template_only: false,
        search: ''
      }
    }
  }
})