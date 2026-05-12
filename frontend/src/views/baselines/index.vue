<!--
  性能基准管理
  ============
  列出所有基准 + 创建入口
-->
<template>
  <div class="fade-in">
    <div class="page-header">
      <div>
        <h1 class="page-title">性能基准</h1>
        <div class="page-subtitle">标记某次任务为基准，用于后续回归对比</div>
      </div>
      <el-button type="primary" @click="openDialog()">新建基准</el-button>
    </div>

    <div class="card">
      <table class="data-table">
        <thead>
          <tr>
            <th>名称</th>
            <th>来源任务</th>
            <th>IOPS</th>
            <th>延迟 (ms)</th>
            <th>带宽 (MB/s)</th>
            <th>容忍度</th>
            <th>状态</th>
            <th style="width: 140px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="b in baselines" :key="b.id">
            <td>
              <div class="cell-title">{{ b.name }}</div>
              <div v-if="b.description" class="cell-sub text-muted">{{ b.description }}</div>
            </td>
            <td>#{{ b.source_task_id }}</td>
            <td>{{ num(b.avg_iops) }}</td>
            <td>{{ num(b.avg_latency_ms) }}</td>
            <td>{{ num(b.avg_bw_mbs) }}</td>
            <td class="text-muted">
              IOPS ±{{ b.iops_tolerance_pct }}% · 延迟 ±{{ b.latency_tolerance_pct }}% · 带宽 ±{{ b.bw_tolerance_pct }}%
            </td>
            <td>
              <span class="tag" :class="b.is_active ? 'tag-success' : 'tag-neutral'">
                {{ b.is_active ? '激活' : '未激活' }}
              </span>
            </td>
            <td>
              <el-button link type="danger" size="small" @click="removeOne(b)">删除</el-button>
            </td>
          </tr>
          <tr v-if="!baselines.length && !loading">
            <td colspan="8" class="text-muted" style="text-align:center; padding:32px">
              暂无基准。在任务详情页把"已完成任务"标记为基准。
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <el-dialog v-model="dialogVisible" title="新建基准" width="520px">
      <el-form :model="form" label-width="140px" label-position="right" size="default">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="例：硬件基准 v1" />
        </el-form-item>
        <el-form-item label="来源任务 ID" required>
          <el-input-number v-model="form.source_task_id" :min="1" style="width:100%" />
          <div class="form-hint">必须是已完成（completed）状态的任务</div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="IOPS 容忍度 %">
          <el-input-number v-model="form.iops_tolerance_pct" :min="0" :max="100" :step="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="延迟容忍度 %">
          <el-input-number v-model="form.latency_tolerance_pct" :min="0" :max="100" :step="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="带宽容忍度 %">
          <el-input-number v-model="form.bw_tolerance_pct" :min="0" :max="100" :step="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="设为激活基准">
          <el-switch v-model="form.is_active" />
          <div class="form-hint">同一测试用例同时只允许一个激活基准（会覆盖旧的）</div>
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
const baselines = ref([])
const dialogVisible = ref(false)
const submitting = ref(false)

const defaultForm = () => ({
  name: '', description: '', source_task_id: null,
  iops_tolerance_pct: 10, latency_tolerance_pct: 10, bw_tolerance_pct: 10,
  is_active: true,
})
const form = ref(defaultForm())

const num = (v) => Number(v || 0).toLocaleString('en-US', { maximumFractionDigits: 2 })

const load = async () => {
  loading.value = true
  try {
    const { data } = await axios.get('/api/baselines')
    baselines.value = Array.isArray(data) ? data : []
  } catch {
    ElMessage.error('获取基准列表失败')
  } finally { loading.value = false }
}

const openDialog = () => {
  form.value = defaultForm()
  dialogVisible.value = true
}

const submit = async () => {
  if (!form.value.name || !form.value.source_task_id) {
    ElMessage.warning('请填写名称和来源任务 ID')
    return
  }
  submitting.value = true
  try {
    await axios.post('/api/baselines', form.value)
    ElMessage.success('基准已创建')
    dialogVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '创建失败')
  } finally { submitting.value = false }
}

const removeOne = async (b) => {
  try {
    await ElMessageBox.confirm(`确认删除基准"${b.name}"？`, '提示', { type: 'warning' })
  } catch { return }
  try {
    await axios.delete(`/api/baselines/${b.id}`)
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
.form-hint { font-size: 12px; color: var(--text-2); margin-top: 2px; }
</style>
