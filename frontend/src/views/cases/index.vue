<template>
  <div class="fade-in">
    <!-- 页面标题和操作 -->
    <div class="page-header">
      <div>
        <h1 class="page-title">用例</h1>
        <div class="page-subtitle">定义 FIO 测试参数模板</div>
      </div>
      <div class="flex items-center gap-2">
        <el-button
          size="default"
          @click="showTemplateDialog = true"
        >
          使用模板
        </el-button>
        <el-button
          size="default"
          @click="handleBatchDelete"
          :disabled="selectedCases.length === 0"
        >
          批量删除
        </el-button>
        <el-button type="primary" size="default" @click="showCreateDialog = true">
          创建用例
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="card p-4">
      <div class="flex flex-wrap items-center gap-4">
        <el-input
          v-model="searchQuery"
          placeholder="搜索用例名称或描述"
          class="flex-1 min-w-64"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <MagnifyingGlassIcon class="w-4 h-4" />
          </template>
        </el-input>
        
        <el-select
          v-model="templateFilter"
          placeholder="类型筛选"
          class="w-32"
          clearable
          @change="handleSearch"
        >
          <el-option label="全部" value="" />
          <el-option label="普通用例" :value="false" />
          <el-option label="模板用例" :value="true" />
        </el-select>
        
        <el-button @click="handleSearch" type="primary">
          搜索
        </el-button>
        <el-button @click="resetFilters">
          重置
        </el-button>
      </div>
    </div>

    <!-- 用例列表 -->
    <div class="card">
      <el-table
        v-loading="loading"
        :data="filteredCases"
        @selection-change="handleSelectionChange"
        style="width: 100%"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column label="用例名称" prop="case_name" min-width="200">
          <template #default="{ row }">
            <div class="flex items-center">
              <div>
                <el-button type="text" class="!text-white font-medium !px-0" @click="handleViewDetail(row)">
                  {{ row.case_name }}
                </el-button>
                <div v-if="row.description" class="text-sm text-slate-400">{{ row.description }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="测试类型" prop="test_type" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="getTestTypeTag(row.test_type)">
              {{ getTestTypeText(row.test_type) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="块大小" prop="block_size" width="100">
          <template #default="{ row }">
            {{ row.block_size || '4k' }}
          </template>
        </el-table-column>
        
        <el-table-column label="队列深度" prop="iodepth" width="100">
          <template #default="{ row }">
            {{ row.iodepth || 1 }}
          </template>
        </el-table-column>
        
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag
              size="small"
              :type="row.is_template ? 'warning' : 'info'"
            >
              {{ row.is_template ? '模板' : '普通' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="创建时间" prop="created_at" width="180">
          <template #default="{ row }">
            <div class="text-slate-300">{{ formatTime(row.created_at) }}</div>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <div class="flex space-x-2">
              <el-button
                type="primary"
                size="small"
                @click="handleClone(row)"
              >
                克隆
              </el-button>
              <el-button
                type="text"
                size="small"
                @click="handleViewCommand(row)"
              >
                命令
              </el-button>
              <el-dropdown trigger="click">
                <el-button type="text" size="small">
                  <EllipsisVerticalIcon class="w-4 h-4" />
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu class="bg-slate-800/95 backdrop-blur-sm border-slate-600/50">
                    <el-dropdown-item @click="handleEdit(row)">
                      <PencilIcon class="w-4 h-4 mr-2" />
                      编辑
                    </el-dropdown-item>
                    <el-dropdown-item @click="handleToggleTemplate(row)">
                      <StarIcon class="w-4 h-4 mr-2" />
                      {{ row.is_template ? '取消模板' : '设为模板' }}
                    </el-dropdown-item>
                    <el-dropdown-item @click="$router.push(`/cases/${row.id}`)">
                      <EyeIcon class="w-4 h-4 mr-2" />
                      详情
                    </el-dropdown-item>
                    <el-dropdown-item divided @click="handleDelete(row)" class="text-danger-400">
                      <TrashIcon class="w-4 h-4 mr-2" />
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="flex items-center justify-between p-4 border-t border-slate-700/50">
        <div class="text-sm text-slate-400">
          共 {{ total }} 个用例
        </div>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="sizes, prev, pager, next"
          @size-change="handlePageChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 创建/编辑用例对话框 -->
    <CaseFormDialog
      v-model="showCreateDialog"
      :case="editingCase"
      @success="handleFormSuccess"
      @close="handleFormClose"
    />

    <!-- 用例详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      :title="`用例详情 - ${viewingCase?.case_name || ''}`"
      width="650px"
      class="case-detail-dialog"
    >
      <div v-if="viewingCase" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-sm text-slate-400">用例名称</label>
            <p class="text-white mt-1">{{ viewingCase.case_name }}</p>
          </div>
          <div>
            <label class="text-sm text-slate-400">测试类型</label>
            <p class="text-white mt-1">{{ getTestTypeText(viewingCase.test_type) }}</p>
          </div>
          <div>
            <label class="text-sm text-slate-400">块大小</label>
            <p class="text-white mt-1">{{ viewingCase.block_size || '4k' }}</p>
          </div>
          <div>
            <label class="text-sm text-slate-400">队列深度</label>
            <p class="text-white mt-1">{{ viewingCase.iodepth || 1 }}</p>
          </div>
          <div>
            <label class="text-sm text-slate-400">作业数</label>
            <p class="text-white mt-1">{{ viewingCase.numjobs || 1 }}</p>
          </div>
          <div>
            <label class="text-sm text-slate-400">运行时长</label>
            <p class="text-white mt-1">{{ viewingCase.runtime || 60 }}秒</p>
          </div>
          <div>
            <label class="text-sm text-slate-400">文件大小</label>
            <p class="text-white mt-1">{{ viewingCase.filesize || '1G' }}</p>
          </div>
          <div>
            <label class="text-sm text-slate-400">类型</label>
            <p class="mt-1">
              <el-tag size="small" :type="viewingCase.is_template ? 'warning' : 'info'">
                {{ viewingCase.is_template ? '模板' : '普通' }}
              </el-tag>
            </p>
          </div>
        </div>
        <div v-if="viewingCase.description">
          <label class="text-sm text-slate-400">描述</label>
          <p class="text-white mt-1">{{ viewingCase.description }}</p>
        </div>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
        <el-button type="primary" @click="handleEditFromDetail">编辑</el-button>
      </template>
    </el-dialog>

    <!-- 模板选择对话框 -->
    <TemplateDialog
      v-model="showTemplateDialog"
      @select="handleTemplateSelect"
    />

    <!-- FIO命令预览对话框 -->
    <CommandDialog
      v-model="showCommandDialog"
      :command="currentCommand"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useCasesStore } from '@stores/cases'
import { ElMessage, ElMessageBox } from 'element-plus'
import CaseFormDialog from './components/CaseFormDialog.vue'
import TemplateDialog from './components/TemplateDialog.vue'
import CommandDialog from './components/CommandDialog.vue'
import {
  MagnifyingGlassIcon,
  EllipsisVerticalIcon,
  PencilIcon,
  TrashIcon,
  StarIcon,
  EyeIcon
} from '@heroicons/vue/24/outline'

const casesStore = useCasesStore()

// 状态
const loading = ref(false)
const searchQuery = ref('')
const templateFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const selectedCases = ref([])
const showCreateDialog = ref(false)
const showTemplateDialog = ref(false)
const showCommandDialog = ref(false)
const showDetailDialog = ref(false)
const viewingCase = ref(null)
const editingCase = ref(null)
const currentCommand = ref('')

// 计算属性
const filteredCases = computed(() => casesStore.filteredCases)
const total = computed(() => casesStore.total)

// 获取测试类型标签
const getTestTypeTag = (testType) => {
  const tags = {
    sequential_read: 'primary',
    sequential_write: 'success',
    random_read: 'warning',
    random_write: 'danger',
    mixed_rw: 'info'
  }
  return tags[testType] || 'info'
}

// 获取测试类型文本
const getTestTypeText = (testType) => {
  const texts = {
    sequential_read: '顺序读',
    sequential_write: '顺序写',
    random_read: '随机读',
    random_write: '随机写',
    mixed_rw: '混合读写'
  }
  return texts[testType] || '未知'
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return '未知'
  return new Date(time).toLocaleString('zh-CN')
}

// 搜索处理
const handleSearch = () => {
  casesStore.setQueryParams({
    search: searchQuery.value,
    template_only: templateFilter.value,
    page: currentPage.value,
    limit: pageSize.value
  })
  casesStore.fetchCases()
}

// 重置筛选
const resetFilters = () => {
  searchQuery.value = ''
  templateFilter.value = ''
  currentPage.value = 1
  pageSize.value = 10
  casesStore.resetQueryParams()
  casesStore.fetchCases()
}

// 分页处理
const handlePageChange = () => {
  handleSearch()
}

// 选择变化处理
const handleSelectionChange = (selection) => {
  selectedCases.value = selection
}

// 克隆用例
const handleClone = async (case_) => {
  try {
    const { value: newName } = await ElMessageBox.prompt(
      '请输入新用例名称',
      '克隆用例',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPlaceholder: `${case_.name}_副本`
      }
    )
    
    if (newName) {
      await casesStore.cloneCase(case_.id, newName)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Clone error:', error)
    }
  }
}

// 查看FIO命令
const handleViewCommand = async (case_) => {
  try {
    const response = await casesStore.getFioCommand(case_.id)
    currentCommand.value = response.command || response.fio_command
    showCommandDialog.value = true
  } catch (error) {
    console.error('Get command error:', error)
  }
}

// 查看用例详情
const handleViewDetail = (case_) => {
  viewingCase.value = case_
  showDetailDialog.value = true
}

// 从详情页编辑
const handleEditFromDetail = () => {
  showDetailDialog.value = false
  editingCase.value = viewingCase.value
  showCreateDialog.value = true
}

// 编辑用例
const handleEdit = (case_) => {
  editingCase.value = case_
  showCreateDialog.value = true
}

// 删除用例
const handleDelete = async (case_) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用例 "${case_.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await casesStore.deleteCase(case_.id)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete error:', error)
    }
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedCases.value.length === 0) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedCases.value.length} 个用例吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const caseIds = selectedCases.value.map(case_ => case_.id)
    await casesStore.batchDeleteCases(caseIds)
    selectedCases.value = []
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Batch delete error:', error)
    }
  }
}

// 切换模板状态
const handleToggleTemplate = async (case_) => {
  try {
    await casesStore.setTemplate(case_.id, !case_.is_template)
  } catch (error) {
    console.error('Toggle template error:', error)
  }
}

// 模板选择
const handleTemplateSelect = (template) => {
  editingCase.value = template
  showCreateDialog.value = true
}

// 表单成功处理
const handleFormSuccess = () => {
  showCreateDialog.value = false
  editingCase.value = null
  casesStore.fetchCases()
}

// 表单关闭处理
const handleFormClose = () => {
  editingCase.value = null
}

// 分区操作成功
const handlePartitionSuccess = () => {
  casesStore.fetchCases()
}

// 初始化
onMounted(() => {
  casesStore.fetchCases()
})
</script>

<style scoped>
.status-tag {
  @apply inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium;
}

.status-online {
  @apply bg-success-900/30 text-success-300 border border-success-700/50;
}

.status-offline {
  @apply bg-danger-900/30 text-danger-300 border border-danger-700/50;
}

.status-pending {
  @apply bg-slate-900/30 text-slate-300 border border-slate-700/50;
}

.animate-fade-in {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.case-detail-dialog {
  @apply bg-slate-800/95 backdrop-blur-sm border-slate-600/50;
}

.case-detail-dialog :deep(.el-dialog__title) {
  @apply text-white;
}

.case-detail-dialog :deep(.el-dialog__body) {
  @apply text-white;
}
</style>