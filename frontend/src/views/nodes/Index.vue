<template>
  <div class="fade-in">
    <!-- 页面标题和操作 -->
    <div class="page-header">
      <div>
        <h1 class="page-title">节点</h1>
        <div class="page-subtitle">管理分布式测试节点的 SSH 连接与健康状态</div>
      </div>
      <div class="flex items-center gap-2">
        <el-button
          size="default"
          @click="showBatchTestDialog = true"
          :disabled="selectedNodes.length === 0"
        >
          批量测试
        </el-button>
        <el-button
          size="default"
          @click="handleBatchDelete"
          :disabled="selectedNodes.length === 0"
        >
          批量删除
        </el-button>
        <el-button type="primary" size="default" @click="showCreateDialog = true">
          添加节点
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="card p-4">
      <div class="flex flex-wrap items-center gap-4">
        <el-input
          v-model="searchQuery"
          placeholder="搜索节点名称或主机地址"
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
          v-model="statusFilter"
          placeholder="状态筛选"
          class="w-32"
          clearable
          @change="handleSearch"
        >
          <el-option label="全部" value="" />
          <el-option label="在线" value="online" />
          <el-option label="离线" value="offline" />
          <el-option label="未知" value="unknown" />
        </el-select>
        
        <el-button @click="handleSearch" type="primary">
          搜索
        </el-button>
        <el-button @click="resetFilters">
          重置
        </el-button>
      </div>
    </div>

    <!-- 节点列表 -->
    <div class="card">
      <el-table
        v-loading="loading"
        :data="filteredNodes"
        @selection-change="handleSelectionChange"
        style="width: 100%"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column label="节点名称" prop="node_name" min-width="150">
          <template #default="{ row }">
            <div class="flex items-center">
              <div :class="getStatusDotClass(row.status)" class="w-3 h-3 rounded-full mr-2"></div>
              <el-button type="text" class="!text-white font-medium !px-0" @click="handleViewDetail(row)">
                {{ row.node_name }}
              </el-button>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="主机地址" prop="host" min-width="150">
          <template #default="{ row }">
            <div class="text-slate-300">{{ row.host }}</div>
            <div class="text-xs text-slate-400">端口: {{ row.port }}</div>
          </template>
        </el-table-column>
        
        <el-table-column label="系统类型" prop="os_type" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="getOSTypeTag(row.os_type)">
              {{ row.os_type || '未知' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="状态" prop="status" width="100">
          <template #default="{ row }">
            <span :class="getStatusClass(row.status)" class="status-tag">
              {{ getStatusText(row.status) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column label="最后检查" prop="last_check" width="150">
          <template #default="{ row }">
            <div class="text-slate-300">{{ formatTime(row.last_check) }}</div>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <div class="flex space-x-2">
              <el-button
                type="primary"
                size="small"
                @click="handleTestConnection(row)"
                :loading="testLoading[row.id]"
              >
                测试连接
              </el-button>
              <el-button
                type="text"
                size="small"
                @click="$router.push(`/nodes/${row.id}`)"
              >
                详情
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
                    <el-dropdown-item @click="handleDelete(row)" class="text-danger-400">
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
          共 {{ total }} 个节点
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

    <!-- 创建/编辑节点对话框 -->
    <NodeFormDialog
      v-model="showCreateDialog"
      :node="editingNode"
      @success="handleFormSuccess"
      @close="handleFormClose"
    />

    <!-- 节点详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      :title="`节点详情 - ${viewingNode?.node_name || ''}`"
      width="600px"
      class="node-detail-dialog"
    >
      <div v-if="viewingNode" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-sm text-slate-400">节点名称</label>
            <p class="text-white mt-1">{{ viewingNode.node_name }}</p>
          </div>
          <div>
            <label class="text-sm text-slate-400">状态</label>
            <p class="mt-1">
              <span :class="getStatusClass(viewingNode.status)" class="status-tag">
                {{ getStatusText(viewingNode.status) }}
              </span>
            </p>
          </div>
          <div>
            <label class="text-sm text-slate-400">主机地址</label>
            <p class="text-white mt-1">{{ viewingNode.host }}:{{ viewingNode.port }}</p>
          </div>
          <div>
            <label class="text-sm text-slate-400">系统类型</label>
            <p class="text-white mt-1">{{ viewingNode.os_type || '未知' }}</p>
          </div>
          <div>
            <label class="text-sm text-slate-400">认证方式</label>
            <p class="text-white mt-1">{{ viewingNode.login_type === 'password' ? '密码认证' : '密钥认证' }}</p>
          </div>
          <div>
            <label class="text-sm text-slate-400">用户名</label>
            <p class="text-white mt-1">{{ viewingNode.username }}</p>
          </div>
          <div>
            <label class="text-sm text-slate-400">最后检查</label>
            <p class="text-white mt-1">{{ formatTime(viewingNode.last_check) }}</p>
          </div>
          <div>
            <label class="text-sm text-slate-400">创建时间</label>
            <p class="text-white mt-1">{{ formatTime(viewingNode.created_at) }}</p>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
        <el-button type="primary" @click="handleEditFromDetail">编辑</el-button>
      </template>
    </el-dialog>

    <!-- 批量测试对话框 -->
    <BatchTestDialog
      v-model="showBatchTestDialog"
      :nodes="selectedNodes"
      @success="handleBatchTestSuccess"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useNodesStore } from '@stores/nodes'
import { ElMessage, ElMessageBox } from 'element-plus'
import NodeFormDialog from './components/NodeFormDialog.vue'
import BatchTestDialog from './components/BatchTestDialog.vue'
import {
  PlusIcon,
  MagnifyingGlassIcon,
  EllipsisVerticalIcon,
  PencilIcon,
  TrashIcon
} from '@heroicons/vue/24/outline'

const nodesStore = useNodesStore()

// 状态
const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const selectedNodes = ref([])
const showCreateDialog = ref(false)
const showBatchTestDialog = ref(false)
const showDetailDialog = ref(false)
const viewingNode = ref(null)
const editingNode = ref(null)
const testLoading = ref({})

// 计算属性
const filteredNodes = computed(() => nodesStore.filteredNodes)
const total = computed(() => nodesStore.total)

// 获取状态点样式
const getStatusDotClass = (status) => {
  const classes = {
    online: 'bg-success-500',
    offline: 'bg-danger-500',
    unknown: 'bg-slate-500'
  }
  return classes[status] || 'bg-slate-500'
}

// 获取状态样式
const getStatusClass = (status) => {
  const classes = {
    online: 'status-online',
    offline: 'status-offline',
    unknown: 'status-pending'
  }
  return classes[status] || 'status-pending'
}

// 获取状态文本
const getStatusText = (status) => {
  const texts = {
    online: '在线',
    offline: '离线',
    unknown: '未知'
  }
  return texts[status] || '未知'
}

// 获取系统类型标签
const getOSTypeTag = (osType) => {
  if (!osType) return 'info'
  if (osType.toLowerCase().includes('linux')) return 'success'
  if (osType.toLowerCase().includes('windows')) return 'primary'
  if (osType.toLowerCase().includes('macos')) return 'warning'
  return 'info'
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return '从未'
  return new Date(time).toLocaleString('zh-CN')
}

// 搜索处理
const handleSearch = () => {
  nodesStore.setQueryParams({
    search: searchQuery.value,
    status_filter: statusFilter.value,
    page: currentPage.value,
    limit: pageSize.value
  })
  nodesStore.fetchNodes()
}

// 重置筛选
const resetFilters = () => {
  searchQuery.value = ''
  statusFilter.value = ''
  currentPage.value = 1
  pageSize.value = 10
  nodesStore.resetQueryParams()
  nodesStore.fetchNodes()
}

// 分页处理
const handlePageChange = () => {
  handleSearch()
}

// 选择变化处理
const handleSelectionChange = (selection) => {
  selectedNodes.value = selection
}

// 测试连接
const handleTestConnection = async (node) => {
  testLoading.value[node.id] = true
  try {
    await nodesStore.testNodeConnection(node.id)
    await nodesStore.fetchNodes()
  } catch (error) {
    console.error('Test connection error:', error)
  } finally {
    testLoading.value[node.id] = false
  }
}

// 查看节点详情
const handleViewDetail = (node) => {
  viewingNode.value = node
  showDetailDialog.value = true
}

// 从详情页编辑
const handleEditFromDetail = () => {
  showDetailDialog.value = false
  editingNode.value = viewingNode.value
  showCreateDialog.value = true
}

// 编辑节点
const handleEdit = (node) => {
  editingNode.value = node
  showCreateDialog.value = true
}

// 删除节点
const handleDelete = async (node) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除节点 "${node.node_name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await nodesStore.deleteNode(node.id)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete error:', error)
    }
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedNodes.value.length === 0) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedNodes.value.length} 个节点吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const nodeIds = selectedNodes.value.map(node => node.id)
    await nodesStore.batchDeleteNodes(nodeIds)
    selectedNodes.value = []
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Batch delete error:', error)
    }
  }
}

// 表单成功处理
const handleFormSuccess = () => {
  showCreateDialog.value = false
  editingNode.value = null
  nodesStore.fetchNodes()
}

// 表单关闭处理
const handleFormClose = () => {
  editingNode.value = null
}

// 批量测试成功处理
const handleBatchTestSuccess = () => {
  showBatchTestDialog.value = false
  nodesStore.fetchNodes()
}

// 初始化
onMounted(() => {
  nodesStore.fetchNodes()
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

.node-detail-dialog {
  @apply bg-slate-800/95 backdrop-blur-sm border-slate-600/50;
}

.node-detail-dialog :deep(.el-dialog__title) {
  @apply text-white;
}

.node-detail-dialog :deep(.el-dialog__body) {
  @apply text-white;
}
</style>