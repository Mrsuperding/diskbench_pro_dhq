<template>
  <div class="fade-in" v-if="node">
    <!-- 返回按钮和标题 -->
    <div class="page-header">
      <div class="flex items-center gap-3">
        <el-button link size="default" @click="$router.back()">
          <ArrowLeftIcon class="w-4 h-4 mr-1" /> 返回
        </el-button>
        <div>
          <h1 class="page-title">{{ node.node_name }}</h1>
          <div class="page-subtitle">节点详细信息和管理</div>
        </div>
      </div>
    </div>

    <!-- 节点信息卡片 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <!-- 基本信息 -->
      <div class="lg:col-span-1">
        <div class="card p-4">
          <h3 class="text-lg font-semibold text-white mb-4">基本信息</h3>
          <div class="space-y-3">
            <div class="flex justify-between">
              <span class="text-slate-400">节点名称</span>
              <span class="text-white">{{ node.node_name }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">主机地址</span>
              <span class="text-white">{{ node.host }}:{{ node.port }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">系统类型</span>
              <el-tag size="small" :type="getOSTypeTag(node.os_type)">
                {{ node.os_type || '未知' }}
              </el-tag>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">认证方式</span>
              <span class="text-white">{{ node.login_type === 'password' ? '密码认证' : '密钥认证' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">用户名</span>
              <span class="text-white">{{ node.username }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">状态</span>
              <span :class="getStatusClass(node.status)" class="status-tag">
                {{ getStatusText(node.status) }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">最后检查</span>
              <span class="text-slate-300">{{ formatTime(node.last_check) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">创建时间</span>
              <span class="text-slate-300">{{ formatTime(node.created_at) }}</span>
            </div>
          </div>
          
          <div class="mt-6 space-y-2">
            <el-button
              type="primary"
              class="w-full"
              @click="handleTestConnection"
              :loading="testLoading"
            >
              测试连接
            </el-button>
            <el-button
              type="warning"
              class="w-full"
              @click="handleEditNode"
            >
              编辑节点
            </el-button>
          </div>
        </div>
      </div>

      <!-- 系统信息 -->
      <div class="lg:col-span-2">
        <div class="card p-4">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-white">系统信息</h3>
            <el-button
              type="primary"
              size="small"
              @click="refreshSystemInfo"
              :loading="refreshingInfo"
            >
              <ArrowPathIcon class="w-4 h-4 mr-1" />
              刷新
            </el-button>
          </div>
          
          <div v-if="systemInfo" class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-3">
              <div class="flex justify-between">
                <span class="text-slate-400">主机名</span>
                <span class="text-white">{{ systemInfo.hostname }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-400">操作系统</span>
                <span class="text-white">{{ systemInfo.os_name }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-400">内核版本</span>
                <span class="text-white">{{ systemInfo.kernel_version }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-400">架构</span>
                <span class="text-white">{{ systemInfo.architecture }}</span>
              </div>
            </div>
            
            <div class="space-y-3">
              <div class="flex justify-between">
                <span class="text-slate-400">CPU核心数</span>
                <span class="text-white">{{ systemInfo.cpu_count }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-400">内存总量</span>
                <span class="text-white">{{ formatBytes(systemInfo.memory_total) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-400">内存可用</span>
                <span class="text-white">{{ formatBytes(systemInfo.memory_available) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-400">负载平均</span>
                <span class="text-white">{{ systemInfo.load_average?.join(', ') }}</span>
              </div>
            </div>
          </div>
          
          <div v-else class="text-center py-8">
            <ServerIcon class="w-12 h-12 text-slate-600 mx-auto mb-2" />
            <p class="text-slate-400">暂无系统信息</p>
            <p class="text-sm text-slate-500 mt-1">点击刷新按钮获取最新信息</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 分区信息 -->
    <div class="card p-4">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-white">磁盘分区</h3>
        <div class="flex space-x-2">
          <el-button
            type="primary"
            size="small"
            @click="refreshPartitions"
            :loading="refreshingPartitions"
          >
            <ArrowPathIcon class="w-4 h-4 mr-1" />
            刷新
          </el-button>
          <el-button
            type="success"
            size="small"
            @click="showAddPartitionDialog = true"
          >
            <PlusIcon class="w-4 h-4 mr-1" />
            添加分区
          </el-button>
        </div>
      </div>
      
      <el-table
        v-if="partitions.length > 0"
        :data="partitions"
        style="width: 100%"
      >
        <el-table-column label="挂载点" prop="mount_point" min-width="150" />
        <el-table-column label="文件系统" prop="filesystem" width="120" />
        <el-table-column label="总大小" width="100">
          <template #default="{ row }">
            {{ formatBytes(row.total_size) }}
          </template>
        </el-table-column>
        <el-table-column label="可用空间" width="100">
          <template #default="{ row }">
            {{ formatBytes(row.available_size) }}
          </template>
        </el-table-column>
        <el-table-column label="使用率" width="120">
          <template #default="{ row }">
            <el-progress
              :percentage="calculateUsage(row)"
              :color="getUsageColor(calculateUsage(row))"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              type="danger"
              size="small"
              text
              @click="handleDeletePartition(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div v-else class="text-center py-8">
        <CircleStackIcon class="w-12 h-12 text-slate-600 mx-auto mb-2" />
        <p class="text-slate-400">暂无分区信息</p>
        <p class="text-sm text-slate-500 mt-1">点击刷新按钮获取分区信息</p>
      </div>
    </div>

    <!-- 节点操作日志 -->
    <div class="card p-4">
      <h3 class="text-lg font-semibold text-white mb-4">操作日志</h3>
      <div class="space-y-3 max-h-64 overflow-y-auto">
        <div
          v-for="log in operationLogs"
          :key="log.id"
          class="flex items-start space-x-3 p-3 rounded-lg bg-slate-700/30"
        >
          <div :class="getLogIconClass(log.type)" class="w-8 h-8 rounded-full flex items-center justify-center mt-0.5">
            <component :is="getLogIcon(log.type)" class="w-4 h-4" />
          </div>
          <div class="flex-1">
            <div class="text-sm text-white">{{ log.message }}</div>
            <div class="text-xs text-slate-400 mt-1">{{ log.timestamp }}</div>
          </div>
        </div>
      </div>
      
      <div v-if="operationLogs.length === 0" class="text-center py-8">
        <ClipboardDocumentListIcon class="w-12 h-12 text-slate-600 mx-auto mb-2" />
        <p class="text-slate-400">暂无操作日志</p>
      </div>
    </div>
  </div>

  <!-- 编辑节点对话框 -->
  <NodeFormDialog
    v-model="showEditDialog"
    :node="node"
    @success="handleEditSuccess"
  />

  <!-- 添加分区对话框 -->
  <PartitionFormDialog
    v-model="showAddPartitionDialog"
    :node-id="nodeId"
    @success="handlePartitionSuccess"
  />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useNodesStore } from '@stores/nodes'
import { ElMessage, ElMessageBox } from 'element-plus'
import NodeFormDialog from './components/NodeFormDialog.vue'
import PartitionFormDialog from './components/PartitionFormDialog.vue'
import {
  ArrowLeftIcon,
  ArrowPathIcon,
  PlusIcon,
  ServerIcon,
  CircleStackIcon,
  ClipboardDocumentListIcon,
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/vue/24/outline'

const route = useRoute()
const nodesStore = useNodesStore()

const nodeId = computed(() => route.params.id)
const node = computed(() => nodesStore.currentNode)

// 状态
const loading = ref(false)
const testLoading = ref(false)
const refreshingInfo = ref(false)
const refreshingPartitions = ref(false)
const showEditDialog = ref(false)
const showAddPartitionDialog = ref(false)

// 模拟数据
const systemInfo = ref({
  hostname: 'test-server-01',
  os_name: 'Ubuntu 22.04.3 LTS',
  kernel_version: '5.15.0-88-generic',
  architecture: 'x86_64',
  cpu_count: 8,
  memory_total: 16777216000,
  memory_available: 12345678900,
  load_average: [0.25, 0.18, 0.15]
})

const partitions = ref([
  {
    id: 1,
    mount_point: '/',
    filesystem: 'ext4',
    total_size: 107374182400,
    available_size: 53687091200
  },
  {
    id: 2,
    mount_point: '/home',
    filesystem: 'ext4',
    total_size: 536870912000,
    available_size: 268435456000
  },
  {
    id: 3,
    mount_point: '/data',
    filesystem: 'xfs',
    total_size: 1099511627776,
    available_size: 549755813888
  }
])

const operationLogs = ref([
  {
    id: 1,
    type: 'info',
    message: '节点连接测试成功',
    timestamp: '2024-01-15 14:30:25'
  },
  {
    id: 2,
    type: 'warning',
    message: '节点连接超时，已重新连接',
    timestamp: '2024-01-15 13:45:12'
  },
  {
    id: 3,
    type: 'success',
    message: '节点信息更新成功',
    timestamp: '2024-01-15 12:20:08'
  },
  {
    id: 4,
    type: 'error',
    message: '节点连接失败：SSH认证失败',
    timestamp: '2024-01-15 11:15:33'
  }
])

// 获取系统类型标签
const getOSTypeTag = (osType) => {
  if (!osType) return 'info'
  if (osType.toLowerCase().includes('linux')) return 'success'
  if (osType.toLowerCase().includes('windows')) return 'primary'
  if (osType.toLowerCase().includes('macos')) return 'warning'
  return 'info'
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

// 格式化时间
const formatTime = (time) => {
  if (!time) return '从未'
  return new Date(time).toLocaleString('zh-CN')
}

// 格式化字节
const formatBytes = (bytes) => {
  if (!bytes) return '0 B'
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}

// 计算使用率
const calculateUsage = (partition) => {
  if (!partition.total_size || !partition.available_size) return 0
  const used = partition.total_size - partition.available_size
  return Math.round((used / partition.total_size) * 100)
}

// 获取使用率颜色
const getUsageColor = (usage) => {
  if (usage < 60) return '#10b981' // success
  if (usage < 80) return '#f59e0b' // warning
  return '#ef4444' // danger
}

// 获取日志图标样式
const getLogIconClass = (type) => {
  const classes = {
    success: 'bg-success-600/20 text-success-400',
    warning: 'bg-warning-600/20 text-warning-400',
    error: 'bg-danger-600/20 text-danger-400',
    info: 'bg-primary-600/20 text-primary-400'
  }
  return classes[type] || classes.info
}

// 获取日志图标
const getLogIcon = (type) => {
  const icons = {
    success: CheckCircleIcon,
    warning: ExclamationTriangleIcon,
    error: XCircleIcon,
    info: InformationCircleIcon
  }
  return icons[type] || InformationCircleIcon
}

// 测试连接
const handleTestConnection = async () => {
  testLoading.value = true
  try {
    await nodesStore.testNodeConnection(nodeId.value)
    await nodesStore.fetchNode(nodeId.value)
  } catch (error) {
    console.error('Test connection error:', error)
  } finally {
    testLoading.value = false
  }
}

// 编辑节点
const handleEditNode = () => {
  showEditDialog.value = true
}

// 编辑成功
const handleEditSuccess = () => {
  nodesStore.fetchNode(nodeId.value)
}

// 刷新系统信息
const refreshSystemInfo = async () => {
  refreshingInfo.value = true
  try {
    // 这里应该调用API获取系统信息
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('系统信息刷新成功')
  } catch (error) {
    ElMessage.error('刷新失败')
  } finally {
    refreshingInfo.value = false
  }
}

// 刷新分区信息
const refreshPartitions = async () => {
  refreshingPartitions.value = true
  try {
    await nodesStore.fetchNodePartitions(nodeId.value)
    ElMessage.success('分区信息刷新成功')
  } catch (error) {
    ElMessage.error('刷新失败')
  } finally {
    refreshingPartitions.value = false
  }
}

// 删除分区
const handleDeletePartition = async (partition) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除分区 "${partition.mount_point}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await nodesStore.deleteNodePartition(nodeId.value, partition.id)
    ElMessage.success('分区删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete partition error:', error)
    }
  }
}

// 分区操作成功
const handlePartitionSuccess = () => {
  nodesStore.fetchNodePartitions(nodeId.value)
}

// 初始化
onMounted(() => {
  nodesStore.fetchNode(nodeId.value)
  nodesStore.fetchNodePartitions(nodeId.value)
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
</style>