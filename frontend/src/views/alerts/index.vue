<!--
  告警管理
  ========
  两个 Tab：规则 / 事件历史
-->
<template>
  <div class="fade-in">
    <div class="page-header">
      <div>
        <h1 class="page-title">告警</h1>
        <div class="page-subtitle">基于阈值的性能异常检测与通知</div>
      </div>
      <el-button v-if="tab === 'rules'" type="primary" @click="openDialog()">新建规则</el-button>
    </div>

    <el-tabs v-model="tab" class="simple-tabs">
      <el-tab-pane label="规则" name="rules">
        <div class="card">
          <table class="data-table">
            <thead>
              <tr>
                <th>名称</th>
                <th>指标</th>
                <th>条件</th>
                <th>范围</th>
                <th>严重程度</th>
                <th>通道</th>
                <th>启用</th>
                <th style="width: 100px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in rules" :key="r.id">
                <td>
                  <div class="cell-title">{{ r.name }}</div>
                  <div v-if="r.description" class="cell-sub text-muted">{{ r.description }}</div>
                </td>
                <td class="text-mono">{{ r.metric }}</td>
                <td class="text-mono">{{ opText(r.operator) }} {{ r.threshold }}</td>
                <td class="text-muted text-sm">
                  <template v-if="r.task_id">task #{{ r.task_id }}</template>
                  <template v-else-if="r.test_case_id">用例 #{{ r.test_case_id }}</template>
                  <template v-else>全部任务</template>
                </td>
                <td>
                  <span class="tag" :class="severityTag(r.severity)">{{ r.severity }}</span>
                </td>
                <td class="text-muted text-sm">{{ (r.channels || []).join(', ') }}</td>
                <td>
                  <el-switch :model-value="r.enabled" size="small" @change="toggle(r, $event)" />
                </td>
                <td>
                  <el-button link type="danger" size="small" @click="removeOne(r)">删除</el-button>
                </td>
              </tr>
              <tr v-if="!rules.length && !loading">
                <td colspan="8" class="text-muted" style="text-align:center; padding:32px">
                  暂无告警规则
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="事件" name="events">
        <div class="card">
          <table class="data-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>严重程度</th>
                <th>任务</th>
                <th>指标</th>
                <th>实际值</th>
                <th>阈值</th>
                <th>消息</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="e in events" :key="e.id">
                <td class="text-muted">{{ fmt(e.triggered_at) }}</td>
                <td><span class="tag" :class="severityTag(e.severity)">{{ e.severity }}</span></td>
                <td>#{{ e.task_id }}</td>
                <td class="text-mono">{{ e.metric }}</td>
                <td class="text-mono">{{ num(e.observed_value) }}</td>
                <td class="text-mono text-muted">{{ num(e.threshold) }}</td>
                <td class="text-muted text-sm">{{ e.message }}</td>
              </tr>
              <tr v-if="!events.length && !loading">
                <td colspan="7" class="text-muted" style="text-align:center; padding:32px">
                  暂无告警事件
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 新建规则对话框 -->
    <el-dialog v-model="dialogVisible" title="新建告警规则" width="560px">
      <el-form :model="form" label-width="120px" label-position="right" size="default">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="例：IOPS 异常下降" />
        </el-form-item>
        <el-form-item label="监控范围">
          <el-radio-group v-model="scope">
            <el-radio-button value="all">全部任务</el-radio-button>
            <el-radio-button value="task">指定任务</el-radio-button>
            <el-radio-button value="case">指定用例</el-radio-button>
          </el-radio-group>
          <div v-if="scope === 'task'" style="margin-top:8px">
            <el-input-number v-model="form.task_id" :min="1" placeholder="任务 ID" style="width:100%" />
          </div>
          <div v-if="scope === 'case'" style="margin-top:8px">
            <el-input-number v-model="form.test_case_id" :min="1" placeholder="用例 ID" style="width:100%" />
          </div>
        </el-form-item>
        <el-form-item label="指标">
          <el-select v-model="form.metric" style="width:100%">
            <el-option value="iops" label="IOPS" />
            <el-option value="bandwidth" label="带宽 (MB/s)" />
            <el-option value="latency" label="延迟 (ms)" />
            <el-option value="cpu_usage" label="CPU 使用率 (%)" />
            <el-option value="memory_usage" label="内存使用率 (%)" />
          </el-select>
        </el-form-item>
        <el-form-item label="条件">
          <el-select v-model="form.operator" style="width:120px">
            <el-option value="gt" label="大于 >" />
            <el-option value="ge" label="大于等于 ≥" />
            <el-option value="lt" label="小于 <" />
            <el-option value="le" label="小于等于 ≤" />
          </el-select>
          <el-input-number v-model="form.threshold" :controls="false" style="flex:1; margin-left:8px" />
        </el-form-item>
        <el-form-item label="连续点数">
          <el-input-number v-model="form.consecutive_points" :min="1" :max="20" style="width:100%" />
          <div class="form-hint">连续 N 个采样点都满足条件才触发，可过滤瞬时毛刺</div>
        </el-form-item>
        <el-form-item label="去重窗口（分钟）">
          <el-input-number v-model="form.dedup_window_minutes" :min="0" style="width:100%" />
        </el-form-item>
        <el-form-item label="严重程度">
          <el-radio-group v-model="form.severity">
            <el-radio-button value="info">info</el-radio-button>
            <el-radio-button value="warning">warning</el-radio-button>
            <el-radio-button value="critical">critical</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="通知通道">
          <el-checkbox-group v-model="form.channels">
            <el-checkbox value="log">log</el-checkbox>
            <el-checkbox value="webhook">webhook</el-checkbox>
            <el-checkbox value="email">email</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item v-if="form.channels.includes('webhook')" label="Webhook URL">
          <el-input v-model="form.webhook_url" placeholder="https://..." />
        </el-form-item>
        <el-form-item v-if="form.channels.includes('email')" label="Email 收件人">
          <el-input v-model="form.email_to" placeholder="ops@example.com" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const tab = ref('rules')
const rules = ref([])
const events = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const submitting = ref(false)
const scope = ref('all')

const defaultForm = () => ({
  name: '', description: '',
  task_id: null, test_case_id: null,
  metric: 'iops', operator: 'lt', threshold: 0,
  consecutive_points: 3, dedup_window_minutes: 5,
  channels: ['log'], webhook_url: '', email_to: '',
  severity: 'warning', enabled: true,
})
const form = ref(defaultForm())

watch(scope, (v) => {
  if (v !== 'task') form.value.task_id = null
  if (v !== 'case') form.value.test_case_id = null
})

const opText = (op) => ({ gt: '>', ge: '≥', lt: '<', le: '≤' }[op] || op)
const severityTag = (s) => ({
  info: 'tag-info', warning: 'tag-warning', critical: 'tag-danger',
}[s] || 'tag-neutral')
const fmt = (s) => s ? String(s).replace('T', ' ').slice(0, 19) : ''
const num = (v) => Number(v || 0).toLocaleString('en-US', { maximumFractionDigits: 2 })

const loadRules = async () => {
  loading.value = true
  try {
    const { data } = await axios.get('/api/alert-rules')
    rules.value = Array.isArray(data) ? data : []
  } catch {
    ElMessage.error('加载规则失败')
  } finally { loading.value = false }
}
const loadEvents = async () => {
  loading.value = true
  try {
    const { data } = await axios.get('/api/alert-events', { params: { page_size: 100 } })
    events.value = data?.items || []
  } catch {
    ElMessage.error('加载事件失败')
  } finally { loading.value = false }
}

const openDialog = () => {
  form.value = defaultForm()
  scope.value = 'all'
  dialogVisible.value = true
}

const submit = async () => {
  if (!form.value.name || form.value.threshold == null) {
    ElMessage.warning('请填写名称和阈值')
    return
  }
  submitting.value = true
  try {
    await axios.post('/api/alert-rules', form.value)
    ElMessage.success('规则已创建')
    dialogVisible.value = false
    loadRules()
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '创建失败')
  } finally { submitting.value = false }
}

const toggle = async (r, val) => {
  try {
    await axios.post(`/api/alert-rules/${r.id}/enable`, null, { params: { enabled: val } })
    r.enabled = val
  } catch { ElMessage.error('操作失败') }
}

const removeOne = async (r) => {
  try {
    await ElMessageBox.confirm(`确认删除规则"${r.name}"？`, '提示', { type: 'warning' })
  } catch { return }
  try {
    await axios.delete(`/api/alert-rules/${r.id}`)
    ElMessage.success('已删除')
    loadRules()
  } catch { ElMessage.error('删除失败') }
}

watch(tab, (v) => {
  if (v === 'rules') loadRules()
  else loadEvents()
})
onMounted(loadRules)
</script>

<style scoped>
.cell-title { font-size: 14px; font-weight: 500; }
.cell-sub { font-size: 12px; margin-top: 2px; }
.text-mono { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 13px; }
.text-sm { font-size: 13px; }
.form-hint { font-size: 12px; color: var(--text-2); margin-top: 2px; }

/* 让 el-tabs 风格也更简洁 */
.simple-tabs :deep(.el-tabs__header) { margin-bottom: 16px; }
.simple-tabs :deep(.el-tabs__nav-wrap::after) { background: var(--border); height: 1px; }
</style>
