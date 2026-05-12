<!--
  调度管理页
  ==========
  简洁表格 + 新建对话框
-->
<template>
  <div class="fade-in">
    <div class="page-header">
      <div>
        <h1 class="page-title">定时调度</h1>
        <div class="page-subtitle">按 once / interval / cron 自动触发测试任务</div>
      </div>
      <el-button type="primary" @click="openDialog()">新建调度</el-button>
    </div>

    <div class="card">
      <table class="data-table">
        <thead>
          <tr>
            <th>名称</th>
            <th>触发</th>
            <th>模板任务</th>
            <th>下次执行</th>
            <th>最近</th>
            <th>启用</th>
            <th style="width: 140px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in schedules" :key="s.id">
            <td>
              <div class="cell-title">{{ s.name }}</div>
              <div v-if="s.description" class="cell-sub text-muted">{{ s.description }}</div>
            </td>
            <td>
              <span class="tag tag-info">{{ s.trigger_type }}</span>
              <span v-if="s.trigger_type === 'cron'" class="ml-1 text-muted text-mono">{{ s.cron_expr }}</span>
              <span v-if="s.trigger_type === 'interval'" class="ml-1 text-muted">每 {{ s.interval_minutes }} 分钟</span>
              <span v-if="s.trigger_type === 'once'" class="ml-1 text-muted">{{ fmt(s.run_at) }}</span>
            </td>
            <td>#{{ s.template_task_id }}</td>
            <td class="text-muted">{{ fmt(s.next_run_at) || '—' }}</td>
            <td>
              <div v-if="s.last_run_at">
                <span class="tag" :class="lastRunTagClass(s.last_run_status)">{{ s.last_run_status || '—' }}</span>
                <div class="cell-sub text-muted">{{ fmt(s.last_run_at) }} · 共 {{ s.run_count }} 次</div>
              </div>
              <span v-else class="text-muted">—</span>
            </td>
            <td>
              <el-switch
                :model-value="s.enabled"
                @change="toggle(s, $event)"
                size="small"
              />
            </td>
            <td>
              <el-button link type="danger" size="small" @click="removeOne(s)">删除</el-button>
            </td>
          </tr>
          <tr v-if="!schedules.length && !loading">
            <td colspan="7" class="text-muted" style="text-align:center; padding:32px">
              暂无调度，点击右上角"新建调度"开始创建
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 新建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" title="新建调度" width="560px">
      <el-form :model="form" label-width="100px" label-position="right" size="default">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="例：夜间基准回归" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="模板任务" required>
          <el-input-number v-model="form.template_task_id" :min="1" style="width: 100%" />
          <div class="form-hint">调度触发时会按此任务的配置克隆并运行一次</div>
        </el-form-item>
        <el-form-item label="触发方式">
          <el-radio-group v-model="form.trigger_type">
            <el-radio-button value="once">单次</el-radio-button>
            <el-radio-button value="interval">间隔</el-radio-button>
            <el-radio-button value="cron">Cron</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="form.trigger_type === 'once'" label="执行时间">
          <el-date-picker v-model="form.run_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width:100%" />
        </el-form-item>

        <template v-if="form.trigger_type === 'interval'">
          <el-form-item label="间隔（分钟）">
            <el-input-number v-model="form.interval_minutes" :min="1" :max="10080" style="width: 100%" />
          </el-form-item>
          <el-form-item label="开始时间">
            <el-date-picker v-model="form.start_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width:100%" />
          </el-form-item>
          <el-form-item label="结束时间">
            <el-date-picker v-model="form.end_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width:100%" />
          </el-form-item>
        </template>

        <el-form-item v-if="form.trigger_type === 'cron'" label="Cron">
          <el-input v-model="form.cron_expr" placeholder="0 2 * * *" class="text-mono" />
          <div class="form-hint">5 字段：分 时 日 月 周。例：<code>0 2 * * *</code> 每天 02:00</div>
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
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const schedules = ref([])
const dialogVisible = ref(false)
const submitting = ref(false)

const defaultForm = () => ({
  name: '', description: '',
  template_task_id: null,
  trigger_type: 'interval',
  interval_minutes: 60,
  cron_expr: '',
  run_at: null, start_at: null, end_at: null,
})
const form = ref(defaultForm())

const fmt = (s) => s ? String(s).replace('T', ' ').slice(0, 16) : ''

const lastRunTagClass = (status) => ({
  success: 'tag-success', failed: 'tag-danger', skipped: 'tag-neutral',
}[status] || 'tag-neutral')

const load = async () => {
  loading.value = true
  try {
    const { data } = await axios.get('/api/schedules')
    schedules.value = Array.isArray(data) ? data : []
  } catch (e) {
    ElMessage.error('获取调度列表失败')
  } finally { loading.value = false }
}

const openDialog = () => {
  form.value = defaultForm()
  dialogVisible.value = true
}

const submit = async () => {
  if (!form.value.name || !form.value.template_task_id) {
    ElMessage.warning('请填写名称和模板任务')
    return
  }
  submitting.value = true
  try {
    await axios.post('/api/schedules', form.value)
    ElMessage.success('调度已创建')
    dialogVisible.value = false
    await load()
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '创建失败')
  } finally { submitting.value = false }
}

const toggle = async (s, val) => {
  try {
    await axios.post(`/api/schedules/${s.id}/enable`, null, { params: { enabled: val } })
    s.enabled = val
  } catch {
    ElMessage.error('操作失败')
  }
}

const removeOne = async (s) => {
  try {
    await ElMessageBox.confirm(`确认删除调度"${s.name}"？`, '提示', { type: 'warning' })
  } catch { return }
  try {
    await axios.delete(`/api/schedules/${s.id}`)
    ElMessage.success('已删除')
    load()
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(load)
</script>

<style scoped>
.cell-title { font-size: 14px; font-weight: 500; }
.cell-sub { font-size: 12px; margin-top: 2px; }
.text-mono { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 12px; }
.form-hint { font-size: 12px; color: var(--text-2); margin-top: 2px; }
.ml-1 { margin-left: 6px; }
code { font-family: ui-monospace, Menlo, Consolas, monospace;
       background: var(--surface-2); padding: 1px 4px; border-radius: 3px; }
</style>
