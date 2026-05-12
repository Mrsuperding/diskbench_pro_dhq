<!--
  运行批次（Run Batch）管理
  =========================
  同一个用例跑 N 次取平均/标准差/CV，评估稳定性
-->
<template>
  <div class="fade-in">
    <div class="page-header">
      <div>
        <h1 class="page-title">运行批次</h1>
        <div class="page-subtitle">对同一任务连续跑 N 次，评估性能稳定性（CV = 标准差/均值）</div>
      </div>
      <el-button type="primary" @click="openDialog()">新建批次</el-button>
    </div>

    <div class="card">
      <table class="data-table">
        <thead>
          <tr>
            <th>名称</th>
            <th>模板任务</th>
            <th>进度</th>
            <th>平均 IOPS</th>
            <th>CV</th>
            <th>状态</th>
            <th>创建时间</th>
            <th style="width: 100px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="b in batches" :key="b.id">
            <td>
              <div class="cell-title">{{ b.name }}</div>
              <div v-if="b.description" class="cell-sub text-muted">{{ b.description }}</div>
            </td>
            <td>#{{ b.template_task_id }}</td>
            <td>
              <div class="flex items-center gap-2">
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: progressOf(b) + '%' }"></div>
                </div>
                <span class="text-muted text-sm whitespace-nowrap">
                  {{ completedCount(b) }}/{{ b.batch_size }}
                </span>
              </div>
            </td>
            <td class="text-mono">{{ num(b.avg_iops) }}</td>
            <td>
              <span :class="cvTag(b.cv_iops)">{{ num(b.cv_iops) }}%</span>
            </td>
            <td>
              <span class="tag" :class="statusTag(b.status)">{{ b.status }}</span>
            </td>
            <td class="text-muted">{{ fmt(b.created_at) }}</td>
            <td>
              <el-button link type="primary" size="small" @click="showDetail(b)">详情</el-button>
            </td>
          </tr>
          <tr v-if="!batches.length && !loading">
            <td colspan="8" class="text-muted" style="text-align:center; padding:32px">
              暂无批次。点击"新建批次"开始
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 新建对话框 -->
    <el-dialog v-model="dialogVisible" title="新建运行批次" width="520px">
      <el-form :model="form" label-width="120px" label-position="right" size="default">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="例：4K 随机读稳定性验证" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="模板任务 ID" required>
          <el-input-number v-model="form.template_task_id" :min="1" style="width: 100%" />
          <div class="form-hint">每次运行会克隆此任务的配置</div>
        </el-form-item>
        <el-form-item label="运行次数">
          <el-input-number v-model="form.batch_size" :min="2" :max="50" style="width: 100%" />
          <div class="form-hint">建议 5–10 次，次数越多越稳定但耗时更久</div>
        </el-form-item>
        <el-form-item label="间隔（秒）">
          <el-input-number v-model="form.interval_seconds" :min="0" :max="3600" style="width: 100%" />
          <div class="form-hint">两次之间休眠时间，让系统状态恢复稳态</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">开始运行</el-button>
      </template>
    </el-dialog>

    <!-- 详情抽屉 -->
    <el-drawer v-model="detailVisible" :title="`批次详情 · ${currentBatch?.name || ''}`" size="640px">
      <div v-if="currentBatch" class="detail-body">
        <!-- 统计摘要 -->
        <div class="stat-summary">
          <div>
            <div class="stat-label">平均 IOPS</div>
            <div class="stat-value">{{ num(currentBatch.avg_iops) }}</div>
          </div>
          <div>
            <div class="stat-label">中位数 IOPS</div>
            <div class="stat-value">{{ num(currentBatch.median_iops) }}</div>
          </div>
          <div>
            <div class="stat-label">标准差</div>
            <div class="stat-value">{{ num(currentBatch.stdev_iops) }}</div>
          </div>
          <div>
            <div class="stat-label">变异系数</div>
            <div class="stat-value" :class="cvTag(currentBatch.cv_iops)">
              {{ num(currentBatch.cv_iops) }}%
            </div>
          </div>
        </div>

        <!-- 各次运行明细 -->
        <h4 class="section-title">各次运行</h4>
        <table class="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Task</th>
              <th>IOPS</th>
              <th>延迟 ms</th>
              <th>带宽 MB/s</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="i in (currentBatch.items || [])" :key="i.id">
              <td>{{ i.run_index }}</td>
              <td>
                <el-button v-if="i.task_id" link type="primary" size="small"
                           @click="$router.push(`/tasks/${i.task_id}`)">
                  #{{ i.task_id }}
                </el-button>
                <span v-else class="text-muted">—</span>
              </td>
              <td class="text-mono">{{ num(i.avg_iops) }}</td>
              <td class="text-mono">{{ num(i.avg_latency_ms) }}</td>
              <td class="text-mono">{{ num(i.avg_bw_mbs) }}</td>
              <td>
                <span class="tag" :class="statusTag(i.status)">{{ i.status }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const batches = ref([])
const dialogVisible = ref(false)
const detailVisible = ref(false)
const submitting = ref(false)
const currentBatch = ref(null)

const defaultForm = () => ({
  name: '', description: '',
  template_task_id: null,
  batch_size: 5,
  interval_seconds: 30,
})
const form = ref(defaultForm())

const num = (v) => Number(v || 0).toLocaleString('en-US', { maximumFractionDigits: 2 })
const fmt = (s) => s ? String(s).replace('T', ' ').slice(0, 16) : ''

const statusTag = (s) => ({
  pending: 'tag-pending', running: 'tag-warning',
  completed: 'tag-success', failed: 'tag-danger', cancelled: 'tag-neutral',
}[s] || 'tag-neutral')

// CV 变异系数的视觉提示：< 5% 优秀，5-15% 一般，> 15% 抖动大
const cvTag = (cv) => {
  const v = Number(cv || 0)
  if (v === 0) return 'text-muted'
  if (v < 5) return 'text-success'
  if (v < 15) return 'text-warning'
  return 'text-danger'
}

const completedCount = (b) => {
  if (!b.items) return b.status === 'completed' ? b.batch_size : 0
  return b.items.filter(i => i.status === 'completed').length
}
const progressOf = (b) => {
  const total = b.batch_size || 1
  return Math.round((completedCount(b) / total) * 100)
}

const load = async () => {
  loading.value = true
  try {
    const { data } = await axios.get('/api/run-batches')
    batches.value = Array.isArray(data) ? data : []
  } catch {
    ElMessage.error('获取批次列表失败')
  } finally { loading.value = false }
}

const openDialog = () => {
  form.value = defaultForm()
  dialogVisible.value = true
}

const submit = async () => {
  if (!form.value.name || !form.value.template_task_id) {
    ElMessage.warning('请填写名称和模板任务 ID')
    return
  }
  submitting.value = true
  try {
    await axios.post('/api/run-batches', form.value)
    ElMessage.success('批次已开始运行')
    dialogVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '创建失败')
  } finally { submitting.value = false }
}

const showDetail = async (b) => {
  try {
    const { data } = await axios.get(`/api/run-batches/${b.id}`)
    currentBatch.value = data
    detailVisible.value = true
  } catch {
    ElMessage.error('获取详情失败')
  }
}

// 自动刷新：running 状态下轮询
let timer = null
onMounted(() => {
  load()
  timer = setInterval(() => {
    if (batches.value.some(b => b.status === 'running' || b.status === 'pending')) {
      load()
    }
  }, 5000)
})
</script>

<style scoped>
.cell-title { font-size: 14px; font-weight: 500; }
.cell-sub { font-size: 12px; margin-top: 2px; }
.text-mono { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 13px; }
.text-sm { font-size: 13px; }
.text-success { color: var(--success); font-weight: 500; }
.text-warning { color: var(--warning); font-weight: 500; }
.text-danger  { color: var(--danger);  font-weight: 500; }
.form-hint { font-size: 12px; color: var(--text-2); margin-top: 2px; }
.flex { display: flex; }
.items-center { align-items: center; }
.gap-2 { gap: 8px; }
.whitespace-nowrap { white-space: nowrap; }

/* 进度条 */
.progress-bar {
  flex: 1;
  min-width: 80px;
  height: 6px;
  background: var(--border-2);
  border-radius: 3px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: var(--brand);
  transition: width .3s;
}

/* 详情抽屉 */
.detail-body { padding: 0 4px; }
.stat-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
  padding: 14px;
  background: var(--surface-2);
  border-radius: var(--radius-lg);
}
.stat-label { font-size: 12px; color: var(--text-2); }
.stat-value { font-size: 18px; font-weight: 600; margin-top: 2px; }
.section-title { font-size: 13px; font-weight: 600; color: var(--text-2);
                 margin: 16px 0 8px; text-transform: uppercase; letter-spacing: .04em; }
</style>
