<!--
  审计日志
  ========
  带过滤器的表格分页列表
-->
<template>
  <div class="fade-in">
    <div class="page-header">
      <div>
        <h1 class="page-title">审计日志</h1>
        <div class="page-subtitle">谁在什么时间对什么资源做了什么操作</div>
      </div>
    </div>

    <!-- 过滤条 -->
    <div class="card">
      <div class="filter-bar">
        <el-input
          v-model="filters.resource_type"
          placeholder="资源类型 (task/node/case...)"
          clearable
          class="filter-input"
          size="default"
          @change="load(1)"
        />
        <el-input
          v-model="filters.resource_id"
          placeholder="资源 ID"
          clearable
          class="filter-input small"
          size="default"
          @change="load(1)"
        />
        <el-input
          v-model="filters.action"
          placeholder="动作 (start/stop/delete...)"
          clearable
          class="filter-input"
          size="default"
          @change="load(1)"
        />
        <el-select
          v-model="filters.status"
          placeholder="状态"
          clearable
          class="filter-input small"
          size="default"
          @change="load(1)"
        >
          <el-option label="成功" value="success" />
          <el-option label="失败" value="failure" />
        </el-select>
        <el-button size="default" @click="reset">重置</el-button>
        <el-button type="primary" size="default" @click="load(1)">查询</el-button>
      </div>
    </div>

    <!-- 表格 -->
    <div class="card">
      <table class="data-table">
        <thead>
          <tr>
            <th style="width: 160px">时间</th>
            <th style="width: 120px">用户</th>
            <th style="width: 90px">状态</th>
            <th style="width: 100px">动作</th>
            <th>资源</th>
            <th>路径</th>
            <th style="width: 120px">来源 IP</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in logs" :key="log.id">
            <td class="text-muted text-mono">{{ fmt(log.created_at) }}</td>
            <td>
              <div v-if="log.username">{{ log.username }}</div>
              <div class="text-subtle text-sm" v-else>{{ log.user_id ? `#${log.user_id}` : '—' }}</div>
            </td>
            <td>
              <span class="tag" :class="statusTag(log.status)">
                <span class="dot" :class="log.status === 'success' ? 'dot-online' : 'dot-offline'" />
                {{ log.status }}
              </span>
            </td>
            <td class="text-mono">{{ log.action }}</td>
            <td>
              <span v-if="log.resource_type" class="tag tag-neutral">{{ log.resource_type }}</span>
              <span v-if="log.resource_id" class="text-muted ml-1">#{{ log.resource_id }}</span>
            </td>
            <td>
              <div class="path-cell">
                <span class="tag-method" :class="'method-' + (log.request_method || '').toLowerCase()">
                  {{ log.request_method }}
                </span>
                <span class="text-mono text-sm text-muted">{{ log.request_path }}</span>
              </div>
              <div v-if="log.message && log.message !== 'HTTP 200'" class="text-subtle text-sm mt-1">
                {{ log.message }}
              </div>
            </td>
            <td class="text-muted text-mono text-sm">{{ log.ip_address || '—' }}</td>
          </tr>
          <tr v-if="!logs.length && !loading">
            <td colspan="7" class="text-muted" style="text-align:center; padding:32px">
              无匹配记录
            </td>
          </tr>
        </tbody>
      </table>

      <!-- 分页 -->
      <div class="pager">
        <span class="text-muted text-sm">共 {{ total }} 条</span>
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next, jumper"
          background
          @current-change="load()"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const logs = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const loading = ref(false)

const filters = ref({
  resource_type: '',
  resource_id: '',
  action: '',
  status: '',
})

const fmt = (s) => s ? String(s).replace('T', ' ').slice(0, 19) : ''

const statusTag = (s) => s === 'success' ? 'tag-success' : 'tag-danger'

const load = async (toPage) => {
  if (toPage) page.value = toPage
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
    }
    for (const [k, v] of Object.entries(filters.value)) {
      if (v !== '' && v != null) params[k] = v
    }
    const { data } = await axios.get('/api/audit-logs', { params })
    logs.value = data?.items || []
    total.value = data?.total || 0
  } catch {
    ElMessage.error('获取审计日志失败')
  } finally { loading.value = false }
}

const reset = () => {
  filters.value = { resource_type: '', resource_id: '', action: '', status: '' }
  load(1)
}

onMounted(() => load())
</script>

<style scoped>
.filter-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  flex-wrap: wrap;
}
.filter-input { width: 200px; }
.filter-input.small { width: 140px; }

.text-mono { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 13px; }
.text-sm { font-size: 13px; }
.text-subtle { color: var(--text-3); }
.mt-1 { margin-top: 4px; }
.ml-1 { margin-left: 4px; }

.path-cell { display: flex; align-items: center; gap: 6px; }

/* HTTP 方法彩签（简洁的颜色提示） */
.tag-method {
  display: inline-block;
  padding: 1px 6px;
  font-family: ui-monospace, Menlo, Consolas, monospace;
  font-size: 11px;
  font-weight: 600;
  border-radius: 3px;
  line-height: 16px;
}
.method-post   { background: var(--success-soft); color: var(--success); }
.method-put    { background: var(--warning-soft); color: var(--warning); }
.method-patch  { background: var(--warning-soft); color: var(--warning); }
.method-delete { background: var(--danger-soft);  color: var(--danger); }
.method-get    { background: var(--info-soft);    color: var(--info); }

/* 分页 */
.pager {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-top: 1px solid var(--border-2);
}
</style>
