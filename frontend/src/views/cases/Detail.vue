<template>
  <div class="fade-in" v-if="case_">
    <!-- 返回按钮和标题 -->
    <div class="page-header">
      <div class="flex items-center gap-3">
        <el-button link size="default" @click="$router.back()">
          <ArrowLeftIcon class="w-4 h-4 mr-1" /> 返回
        </el-button>
        <div>
          <h1 class="page-title">{{ case_.name }}</h1>
          <div class="page-subtitle">用例详细信息和配置</div>
        </div>
      </div>
    </div>

    <!-- 基本信息卡片 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <!-- 基本信息 -->
      <div class="lg:col-span-1">
        <div class="card p-4">
          <h3 class="text-lg font-semibold text-white mb-4">基本信息</h3>
          <div class="space-y-3">
            <div class="flex justify-between">
              <span class="text-slate-400">用例名称</span>
              <span class="text-white">{{ case_.name }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">测试类型</span>
              <el-tag size="small" :type="getTestTypeTag(case_.test_type)">
                {{ getTestTypeText(case_.test_type) }}
              </el-tag>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">类型</span>
              <el-tag
                size="small"
                :type="case_.is_template ? 'warning' : 'info'"
              >
                {{ case_.is_template ? '模板' : '普通' }}
              </el-tag>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">创建时间</span>
              <span class="text-slate-300">{{ formatTime(case_.created_at) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-400">更新时间</span>
              <span class="text-slate-300">{{ formatTime(case_.updated_at) }}</span>
            </div>
          </div>
          
          <div class="mt-6 space-y-2">
            <el-button
              type="primary"
              class="w-full"
              @click="handleClone"
            >
              克隆用例
            </el-button>
            <el-button
              type="success"
              class="w-full"
              @click="handleToggleTemplate"
            >
              {{ case_.is_template ? '取消模板' : '设为模板' }}
            </el-button>
            <el-button
              type="warning"
              class="w-full"
              @click="handleEdit"
            >
              编辑用例
            </el-button>
          </div>
        </div>
      </div>

      <!-- FIO参数配置 -->
      <div class="lg:col-span-2">
        <div class="card p-4">
          <h3 class="text-lg font-semibold text-white mb-4">FIO参数配置</h3>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-4">
              <h4 class="text-white font-medium">基本参数</h4>
              <div class="space-y-3">
                <div class="flex justify-between">
                  <span class="text-slate-400">块大小</span>
                  <span class="text-white">{{ case_.block_size || '4k' }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-slate-400">队列深度</span>
                  <span class="text-white">{{ case_.iodepth || 1 }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-slate-400">线程数</span>
                  <span class="text-white">{{ case_.numjobs || 1 }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-slate-400">测试时间</span>
                  <span class="text-white">{{ case_.runtime || 60 }}秒</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-slate-400">文件大小</span>
                  <span class="text-white">{{ case_.filesize || '1G' }}</span>
                </div>
              </div>
            </div>
            
            <div class="space-y-4">
              <h4 class="text-white font-medium">高级参数</h4>
              <div class="space-y-3">
                <div class="flex justify-between">
                  <span class="text-slate-400">读写比例</span>
                  <span class="text-white">{{ case_.rwmixread || 50 }}%</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-slate-400">直接IO</span>
                  <el-tag size="small" :type="case_.direct ? 'success' : 'info'">
                    {{ case_.direct ? '开启' : '关闭' }}
                  </el-tag>
                </div>
                <div class="flex justify-between">
                  <span class="text-slate-400">同步IO</span>
                  <el-tag size="small" :type="case_.sync ? 'success' : 'info'">
                    {{ case_.sync ? '开启' : '关闭' }}
                  </el-tag>
                </div>
                <div class="flex justify-between">
                  <span class="text-slate-400">验证数据</span>
                  <el-tag size="small" :type="case_.verify ? 'success' : 'info'">
                    {{ case_.verify ? '开启' : '关闭' }}
                  </el-tag>
                </div>
                <div class="flex justify-between">
                  <span class="text-slate-400">时间基准</span>
                  <el-tag size="small" :type="case_.time_based ? 'success' : 'info'">
                    {{ case_.time_based ? '开启' : '关闭' }}
                  </el-tag>
                </div>
                <div class="flex justify-between">
                  <span class="text-slate-400">覆盖文件</span>
                  <el-tag size="small" :type="case_.overwrite ? 'success' : 'info'">
                    {{ case_.overwrite ? '开启' : '关闭' }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- FIO命令预览 -->
    <div class="card p-4">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-white">FIO命令预览</h3>
        <div class="flex space-x-2">
          <el-button
            type="primary"
            size="small"
            @click="copyCommand"
          >
            <ClipboardDocumentIcon class="w-4 h-4 mr-1" />
            复制命令
          </el-button>
          <el-button
            type="success"
            size="small"
            @click="createTask"
          >
            <PlusIcon class="w-4 h-4 mr-1" />
            创建任务
          </el-button>
        </div>
      </div>
      
      <div class="code-block">
        <pre>{{ fioCommand }}</pre>
      </div>
      
      <div class="mt-4 bg-slate-700/30 p-4 rounded-lg">
        <h4 class="text-white font-medium mb-2">参数说明</h4>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-slate-300">
          <div><code class="text-primary-400">--name</code>: 测试任务名称</div>
          <div><code class="text-primary-400">--filename</code>: 测试文件路径</div>
          <div><code class="text-primary-400">--bs</code>: 块大小</div>
          <div><code class="text-primary-400">--iodepth</code>: 队列深度</div>
          <div><code class="text-primary-400">--numjobs</code>: 并发线程数</div>
          <div><code class="text-primary-400">--runtime</code>: 测试运行时间</div>
          <div><code class="text-primary-400">--rw</code>: 读写模式</div>
          <div><code class="text-primary-400">--output-format</code>: 输出格式</div>
        </div>
      </div>
    </div>

    <!-- 使用统计 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div class="card p-4">
        <h3 class="text-lg font-semibold text-white mb-4">使用统计</h3>
        <div class="space-y-3">
          <div class="flex justify-between">
            <span class="text-slate-400">使用次数</span>
            <span class="text-white">{{ caseStats.usage_count || 0 }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-slate-400">成功次数</span>
            <span class="text-success-400">{{ caseStats.success_count || 0 }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-slate-400">失败次数</span>
            <span class="text-danger-400">{{ caseStats.failure_count || 0 }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-slate-400">成功率</span>
            <span class="text-white">{{ calculateSuccessRate }}%</span>
          </div>
          <div class="flex justify-between">
            <span class="text-slate-400">最近使用</span>
            <span class="text-slate-300">{{ formatTime(caseStats.last_used) }}</span>
          </div>
        </div>
      </div>

      <div class="card p-4">
        <h3 class="text-lg font-semibold text-white mb-4">最近任务</h3>
        <div v-if="recentTasks.length > 0" class="space-y-3">
          <div
            v-for="task in recentTasks"
            :key="task.id"
            class="flex items-center justify-between p-3 rounded-lg bg-slate-700/30"
          >
            <div>
              <div class="text-white font-medium">{{ task.name }}</div>
              <div class="text-sm text-slate-400">{{ task.created_at }}</div>
            </div>
            <div>
              <span :class="getStatusClass(task.status)" class="status-tag">
                {{ getStatusText(task.status) }}
              </span>
            </div>
          </div>
        </div>
        
        <div v-else class="text-center py-8">
          <ClipboardDocumentListIcon class="w-12 h-12 text-slate-600 mx-auto mb-2" />
          <p class="text-slate-400">暂无任务记录</p>
        </div>
      </div>
    </div>
  </div>

  <!-- 编辑用例对话框 -->
  <CaseFormDialog
    v-model="showEditDialog"
    :case="case_"
    @success="handleEditSuccess"
  />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCasesStore } from '@stores/cases'
import { ElMessage, ElMessageBox } from 'element-plus'
import CaseFormDialog from './components/CaseFormDialog.vue'
import {
  ArrowLeftIcon,
  ClipboardDocumentIcon,
  PlusIcon,
  DocumentTextIcon,
  ClipboardDocumentListIcon,
  StarIcon,
  PencilIcon
} from '@heroicons/vue/24/outline'

const route = useRoute()
const router = useRouter()
const casesStore = useCasesStore()

const caseId = computed(() => route.params.id)
const case_ = computed(() => casesStore.currentCase)

// 状态
const loading = ref(false)
const showEditDialog = ref(false)

// 模拟数据
const fioCommand = ref('')
const caseStats = ref({
  usage_count: 15,
  success_count: 13,
  failure_count: 2,
  last_used: '2024-01-15 14:30:25'
})

const recentTasks = ref([
  {
    id: 1,
    name: 'SSD性能测试-2024-01-15',
    status: 'completed',
    created_at: '2024-01-15 14:30'
  },
  {
    id: 2,
    name: 'HDD基准测试-2024-01-14',
    status: 'completed',
    created_at: '2024-01-14 16:20'
  },
  {
    id: 3,
    name: 'NVMe压力测试-2024-01-13',
    status: 'failed',
    created_at: '2024-01-13 10:15'
  }
])

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

// 获取状态样式
const getStatusClass = (status) => {
  const classes = {
    pending: 'status-pending',
    running: 'status-running',
    completed: 'status-completed',
    failed: 'status-offline'
  }
  return classes[status] || 'status-pending'
}

// 获取状态文本
const getStatusText = (status) => {
  const texts = {
    pending: '待执行',
    running: '运行中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || '未知'
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return '从未'
  return new Date(time).toLocaleString('zh-CN')
}

// 计算成功率
const calculateSuccessRate = computed(() => {
  const total = caseStats.value.usage_count || 0
  const success = caseStats.value.success_count || 0
  return total > 0 ? Math.round((success / total) * 100) : 0
})

// 生成FIO命令
const generateFioCommand = () => {
  if (!case_.value) return ''
  
  const params = []
  
  // 基本参数
  params.push(`--name=${case_.value.name || 'test'}`)
  params.push(`--filename=testfile`)
  params.push(`--bs=${case_.value.block_size || '4k'}`)
  params.push(`--iodepth=${case_.value.iodepth || 1}`)
  params.push(`--numjobs=${case_.value.numjobs || 1}`)
  params.push(`--runtime=${case_.value.runtime || 60}`)
  params.push(`--size=${case_.value.filesize || '1G'}`)
  
  // 测试类型
  const rwMap = {
    sequential_read: 'read',
    sequential_write: 'write',
    random_read: 'randread',
    random_write: 'randwrite',
    mixed_rw: 'randrw'
  }
  params.push(`--rw=${rwMap[case_.value.test_type] || 'read'}`)
  
  // 混合读写比例
  if (case_.value.test_type === 'mixed_rw') {
    params.push(`--rwmixread=${case_.value.rwmixread || 50}`)
  }
  
  // 开关参数
  if (case_.value.direct) params.push('--direct=1')
  if (case_.value.sync) params.push('--sync=1')
  if (case_.value.verify) params.push('--verify=1')
  if (case_.value.time_based) params.push('--time_based=1')
  if (case_.value.overwrite) params.push('--overwrite=1')
  
  // 输出格式
  params.push('--output-format=json')
  params.push('--group_reporting')
  
  fioCommand.value = `fio ${params.join(' ')}`
}

// 复制命令
const copyCommand = async () => {
  try {
    await navigator.clipboard.writeText(fioCommand.value)
    ElMessage.success('命令已复制到剪贴板')
  } catch (error) {
    console.error('Copy failed:', error)
    ElMessage.error('复制失败')
  }
}

// 克隆用例
const handleClone = async () => {
  try {
    const { value: newName } = await ElMessageBox.prompt(
      '请输入新用例名称',
      '克隆用例',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPlaceholder: `${case_.value.name}_副本`
      }
    )
    
    if (newName) {
      await casesStore.cloneCase(case_.value.id, newName)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Clone error:', error)
    }
  }
}

// 切换模板状态
const handleToggleTemplate = async () => {
  try {
    await casesStore.setTemplate(case_.value.id, !case_.value.is_template)
  } catch (error) {
    console.error('Toggle template error:', error)
  }
}

// 编辑用例
const handleEdit = () => {
  showEditDialog.value = true
}

// 编辑成功
const handleEditSuccess = () => {
  casesStore.fetchCase(caseId.value)
}

// 创建任务
const createTask = () => {
  router.push({
    name: 'Tasks',
    query: {
      caseId: case_.value.id
    }
  })
}

// 初始化
onMounted(() => {
  casesStore.fetchCase(caseId.value)
  generateFioCommand()
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

.status-running {
  @apply bg-warning-900/30 text-warning-300 border border-warning-700/50;
}

.status-completed {
  @apply bg-success-900/30 text-success-300 border border-success-700/50;
}

.status-pending {
  @apply bg-slate-900/30 text-slate-300 border border-slate-700/50;
}

.code-block {
  @apply bg-slate-900/50 text-slate-200 p-4 rounded-lg font-mono text-sm overflow-x-auto;
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