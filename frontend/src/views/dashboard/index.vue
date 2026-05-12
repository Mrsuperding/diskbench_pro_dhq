<!--
  Dashboard · 概览
  ================
  改进：
  - 4 张统计卡改成一行扁平卡片（不再有巨大图标色块）
  - 快速入口用文字按钮，不用大色块
  - "最近任务"用标准表格呈现
  - 整页不再使用毛玻璃/渐变
-->
<template>
  <div class="dashboard fade-in">
    <!-- 顶部标题 -->
    <div class="page-header">
      <div>
        <h1 class="page-title">概览</h1>
        <div class="page-subtitle">系统资源、测试任务与运行状态一览</div>
      </div>
      <div class="flex items-center gap-2">
        <el-button size="default" @click="refresh" :loading="loading">刷新</el-button>
        <el-button type="primary" size="default" @click="$router.push('/tasks/create')">
          新建任务
        </el-button>
      </div>
    </div>

    <!-- ====== 统计指标 ====== -->
    <div class="stat-grid">
      <div class="card stat-card">
        <div class="stat-label">节点</div>
        <div class="stat-value">{{ stats.totalNodes }}</div>
        <div class="stat-footer">
          <span class="tag tag-success">{{ stats.onlineNodes }} 在线</span>
          <span class="tag tag-danger">{{ stats.offlineNodes }} 离线</span>
        </div>
      </div>

      <div class="card stat-card">
        <div class="stat-label">测试用例</div>
        <div class="stat-value">{{ stats.totalCases }}</div>
        <div class="stat-footer text-muted">
          模板 {{ stats.templateCases }}
        </div>
      </div>

      <div class="card stat-card">
        <div class="stat-label">测试任务</div>
        <div class="stat-value">{{ stats.totalTasks }}</div>
        <div class="stat-footer">
          <span class="tag tag-warning">
            <span class="dot dot-running" /> {{ stats.runningTasks }} 运行中
          </span>
        </div>
      </div>

      <div class="card stat-card">
        <div class="stat-label">用户</div>
        <div class="stat-value">{{ stats.totalUsers }}</div>
        <div class="stat-footer text-muted">
          管理员 {{ stats.adminUsers }}
        </div>
      </div>
    </div>

    <!-- ====== 两栏：快速入口 + 最近任务 ====== -->
    <div class="two-col">
      <!-- 快速入口 -->
      <div class="card">
        <div class="card-header">
          <h3>快速入口</h3>
        </div>
        <div class="card-body quick-actions">
          <router-link to="/nodes" class="quick-item">
            <span class="quick-title">添加节点</span>
            <span class="quick-desc">配置可执行测试的主机</span>
          </router-link>
          <router-link to="/cases/create" class="quick-item">
            <span class="quick-title">创建用例</span>
            <span class="quick-desc">定义 FIO 测试参数</span>
          </router-link>
          <router-link to="/tasks/create" class="quick-item">
            <span class="quick-title">启动任务</span>
            <span class="quick-desc">选择用例并下发执行</span>
          </router-link>
          <router-link to="/schedules" class="quick-item">
            <span class="quick-title">定时调度</span>
            <span class="quick-desc">周期性自动跑任务</span>
          </router-link>
          <router-link to="/baselines" class="quick-item">
            <span class="quick-title">性能基准</span>
            <span class="quick-desc">回归对比历史结果</span>
          </router-link>
          <router-link to="/monitor" class="quick-item">
            <span class="quick-title">实时监控</span>
            <span class="quick-desc">查看性能抖动图</span>
          </router-link>
        </div>
      </div>

      <!-- 最近任务 -->
      <div class="card">
        <div class="card-header">
          <h3>最近任务</h3>
          <router-link to="/tasks" class="text-brand text-sm">查看全部 →</router-link>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>任务名称</th>
              <th style="width: 100px">状态</th>
              <th style="width: 140px">创建时间</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="t in recentTasks"
              :key="t.id"
              class="cursor-pointer"
              @click="$router.push(`/tasks/${t.id}`)"
            >
              <td>{{ t.name }}</td>
              <td>
                <span class="tag" :class="statusTagClass(t.status)">
                  <span class="dot" :class="statusDotClass(t.status)" />
                  {{ statusText(t.status) }}
                </span>
              </td>
              <td class="text-muted">{{ t.created_at }}</td>
            </tr>
            <tr v-if="!recentTasks.length">
              <td colspan="3" class="text-muted" style="text-align:center; padding: 24px;">
                暂无任务
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ====== 系统信息 ====== -->
    <div class="card sys-info">
      <div class="card-body sys-info-body">
        <div>
          <div class="stat-label">系统运行时间</div>
          <div class="sys-info-value">{{ systemUptime }}</div>
        </div>
        <div>
          <div class="stat-label">版本</div>
          <div class="sys-info-value">v1.2.0</div>
        </div>
        <div>
          <div class="stat-label">后台服务</div>
          <div class="flex items-center gap-2 mt-1">
            <span class="tag tag-success"><span class="dot dot-online" /> 健康检查</span>
            <span class="tag tag-success"><span class="dot dot-online" /> 调度器</span>
            <span class="tag tag-success"><span class="dot dot-online" /> 保留策略</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const loading = ref(false)
const stats = ref({
  totalNodes: 0, onlineNodes: 0, offlineNodes: 0,
  totalCases: 0, templateCases: 0,
  totalTasks: 0, runningTasks: 0,
  totalUsers: 0, adminUsers: 0,
})
const recentTasks = ref([])
const systemUptime = ref('—')

const statusText = (s) => ({
  pending: '待执行', running: '运行中', completed: '已完成',
  failed: '失败', cancelled: '已取消',
}[s] || s)

const statusTagClass = (s) => ({
  pending: 'tag-pending',
  running: 'tag-warning',
  completed: 'tag-success',
  failed: 'tag-danger',
  cancelled: 'tag-neutral',
}[s] || 'tag-neutral')

const statusDotClass = (s) => ({
  pending: '',
  running: 'dot-running',
  completed: 'dot-online',
  failed: 'dot-offline',
}[s] || '')

const refresh = async () => {
  loading.value = true
  try {
    // TODO: 对接真实接口
    // const { data } = await axios.get('/api/admin/dashboard')
    // stats.value = data.stats
    // recentTasks.value = data.recent_tasks
    // 暂时保持占位数据
  } finally {
    loading.value = false
  }
}

let timer = null
onMounted(() => {
  refresh()
  timer = setInterval(refresh, 30000)
})
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<style scoped>
.dashboard { display: flex; flex-direction: column; gap: 16px; }

/* 统计卡片网格 */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}
.stat-card {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* 两栏布局 */
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
@media (max-width: 1024px) {
  .two-col { grid-template-columns: 1fr; }
}

/* 快速入口 */
.quick-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1px;
  padding: 0;
  background: var(--border-2);
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
  overflow: hidden;
}
.quick-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 14px 16px;
  background: var(--surface);
  text-decoration: none;
  color: var(--text);
  transition: background .12s;
  cursor: pointer;
}
.quick-item:hover { background: var(--brand-soft); }
.quick-title { font-size: 14px; font-weight: 500; }
.quick-desc { font-size: 12px; color: var(--text-2); }

/* 系统信息栏 */
.sys-info-body {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}
.sys-info-value {
  font-size: 15px;
  font-weight: 500;
  color: var(--text);
  margin-top: 2px;
}

/* 小工具 */
.flex { display: flex; }
.items-center { align-items: center; }
.gap-2 { gap: 8px; }
.mt-1 { margin-top: 4px; }
.text-sm { font-size: 13px; }
.cursor-pointer { cursor: pointer; }
</style>
