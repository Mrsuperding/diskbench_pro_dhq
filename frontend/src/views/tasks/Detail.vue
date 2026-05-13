<template>
  <div class="task-detail" v-if="task">
    <!-- 头部 -->
    <div class="detail-header">
      <div class="header-left">
        <el-button link @click="$router.back()" class="back-btn">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
          返回
        </el-button>
      </div>
      <div class="header-center">
        <h1>{{ task.task_name }}</h1>
        <div class="header-meta">
          <span :class="['status-badge', `status-${task.status}`]">{{ getStatusText(task.status) }}</span>
          <span class="meta-divider">|</span>
          <span class="meta-item">ID: {{ task.id }}</span>
          <span class="meta-divider">|</span>
          <span class="meta-item">创建于 {{ formatTime(task.created_at) }}</span>
        </div>
      </div>
      <div class="header-right">
        <el-button v-if="task.status === 'pending' || task.status === 'running'" type="success" @click="handleStart" :disabled="task.status === 'running'">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          启动
        </el-button>
        <el-button v-if="task.status === 'running'" type="warning" @click="handleStop">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
          停止
        </el-button>
        <el-button type="danger" @click="handleDelete">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          删除
        </el-button>
      </div>
    </div>

    <!-- 指标卡片 -->
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-icon iops">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ formatNumber(task.avg_iops) }}</div>
          <div class="metric-label">IOPS</div>
        </div>
      </div>
      <div class="metric-card">
        <div class="metric-icon bw">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ formatBw(task.avg_bw) }}</div>
          <div class="metric-label">带宽</div>
        </div>
      </div>
      <div class="metric-card">
        <div class="metric-icon latency">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ formatLatency(task.avg_latency) }}</div>
          <div class="metric-label">延迟</div>
        </div>
      </div>
      <div class="metric-card">
        <div class="metric-icon duration">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ formatDuration(task.duration) }}</div>
          <div class="metric-label">运行时长</div>
        </div>
      </div>
    </div>

    <!-- Tab 导航 -->
    <div class="tab-navigation">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        <component :is="tab.icon" />
        <span>{{ tab.label }}</span>
        <span v-if="tab.count !== undefined" class="tab-count">{{ tab.count }}</span>
      </button>
    </div>

    <!-- Tab 内容 -->
    <div class="tab-content">
      <!-- 基本信息 Tab -->
      <div v-show="activeTab === 'info'" class="tab-panel">
        <div class="info-section">
          <h3>基本信息</h3>
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">任务ID</span>
              <span class="info-value">{{ task.id }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">任务名称</span>
              <span class="info-value">{{ task.task_name }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">状态</span>
              <span :class="['status-text', `status-${task.status}`]">{{ getStatusText(task.status) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">节点数</span>
              <span class="info-value">{{ taskNodes.length }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">创建时间</span>
              <span class="info-value">{{ formatTime(task.created_at) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">开始时间</span>
              <span class="info-value">{{ task.start_time ? formatTime(task.start_time) : '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">结束时间</span>
              <span class="info-value">{{ task.end_time ? formatTime(task.end_time) : '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">总IO</span>
              <span class="info-value">{{ formatNumber(task.total_io_ops) }}</span>
            </div>
          </div>
        </div>
        <div v-if="task.description" class="info-section">
          <h3>描述</h3>
          <p class="description-text">{{ task.description }}</p>
        </div>
      </div>

      <!-- 节点 Tab -->
      <div v-show="activeTab === 'nodes'" class="tab-panel">
        <div class="section-header">
          <div class="section-title">
            <h3>关联节点</h3>
            <span class="node-count">共 {{ taskNodes.length }} 个节点</span>
          </div>
          <el-button type="primary" @click="showAddNodeDialog">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            添加节点
          </el-button>
        </div>
        <el-table :data="taskNodes" border class="node-table" v-if="taskNodes.length > 0">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column label="节点" min-width="150">
            <template #default="{ row }">
              <el-button type="text" class="!text-white font-medium !px-0" @click="handleEditNodePartitions(row)">
                {{ row.node?.name || `节点 ${row.node_id}` }}
              </el-button>
              <div class="text-xs text-slate-400">{{ row.node?.host || '' }}</div>
            </template>
          </el-table-column>
          <el-table-column label="分区" min-width="150">
            <template #default="{ row }">
              <span>{{ row.partitions || row.partition?.mount_point || `分区 ${row.partition_id}` }}</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <span :class="['node-status', `status-${row.status}`]">{{ getStatusText(row.status) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="IOPS" width="100">
            <template #default="{ row }">{{ formatNumber(row.iops) }}</template>
          </el-table-column>
          <el-table-column label="带宽" width="100">
            <template #default="{ row }">{{ formatBw(row.bandwidth) }}</template>
          </el-table-column>
          <el-table-column label="延迟" width="100">
            <template #default="{ row }">{{ formatLatency(row.latency) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ row }">
              <el-button type="danger" size="small" @click="handleRemoveNode(row)">移除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div v-else class="empty-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>
          <p>暂无关联节点</p>
          <el-button type="primary" @click="showAddNodeDialog">添加第一个节点</el-button>
        </div>
      </div>

      <!-- 用例 Tab -->
      <div v-show="activeTab === 'case'" class="tab-panel">
        <div class="section-header">
          <div class="section-title">
            <h3>测试用例配置</h3>
            <span class="node-count">每个用例会生成多个测试任务</span>
          </div>
          <el-button type="primary" @click="showAddCaseDialog">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            添加用例配置
          </el-button>
        </div>

        <!-- 用例列表 -->
        <div class="case-list" v-if="taskCases.length > 0">
          <div v-for="(tc, index) in taskCases" :key="index" class="case-card">
            <div class="case-card-header">
              <span class="case-index">用例 {{ index + 1 }}</span>
              <div class="case-actions">
                <el-button size="small" @click="editCaseConfig(tc)">编辑</el-button>
                <el-button size="small" type="danger" @click="removeCaseConfig(index)">删除</el-button>
              </div>
            </div>
            <div class="case-card-content">
              <div class="case-row">
                <span class="case-label">IO引擎</span>
                <span class="case-value">{{ tc.io_engine || 'libaio' }}</span>
              </div>
              <div class="case-row">
                <span class="case-label">块大小</span>
                <div class="multi-values">
                  <span v-for="bs in tc.block_sizes" :key="bs" class="value-tag">{{ bs }}</span>
                </div>
              </div>
              <div class="case-row">
                <span class="case-label">IO模式</span>
                <div class="multi-values">
                  <span v-for="rw in tc.rw_modes" :key="rw" class="value-tag mode">{{ getRwModeText(rw) }}</span>
                </div>
              </div>
              <div class="case-row">
                <span class="case-label">队列深度</span>
                <span class="case-value">{{ tc.queue_depth || 32 }}</span>
              </div>
              <div class="case-row">
                <span class="case-label">IO大小</span>
                <span class="case-value">{{ tc.io_size || '1G' }}</span>
              </div>
              <div class="case-row">
                <span class="case-label">运行时长</span>
                <span class="case-value">{{ tc.runtime || 60 }}秒</span>
              </div>
              <div class="case-row">
                <span class="case-label">Numjobs</span>
                <span class="case-value">{{ tc.numjobs || 1 }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
          <p>暂无用例配置</p>
          <el-button type="primary" @click="showAddCaseDialog">添加第一个用例</el-button>
        </div>
      </div>

      <!-- 性能详情 Tab -->
      <div v-show="activeTab === 'percentiles'" class="tab-panel">
        <div class="section-header">
          <div class="section-title">
            <h3>百分位延迟</h3>
            <span class="node-count">共 {{ percentileData.length }} 条数据</span>
          </div>
          <el-button @click="loadPercentiles">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
            刷新
          </el-button>
        </div>
        <div class="percentile-table" v-if="percentileData.length > 0">
          <table>
            <thead>
              <tr>
                <th>节点</th>
                <th>类型</th>
                <th>p1</th>
                <th>p50</th>
                <th>p75</th>
                <th>p90</th>
                <th>p95</th>
                <th>p99</th>
                <th>p999</th>
                <th>p9999</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="nodePercentiles in groupedPercentiles" :key="nodePercentiles.node_id">
                <tr v-for="(item, idx) in nodePercentiles.data" :key="idx">
                  <td v-if="idx === 0" :rowspan="nodePercentiles.data.length">{{ nodePercentiles.node_name }}</td>
                  <td>{{ item.test_type }}</td>
                  <td>{{ formatLatency(getPercentile(item, item.test_type, 'p1')) }}</td>
                  <td>{{ formatLatency(getPercentile(item, item.test_type, 'p50')) }}</td>
                  <td>{{ formatLatency(getPercentile(item, item.test_type, 'p75')) }}</td>
                  <td>{{ formatLatency(getPercentile(item, item.test_type, 'p90')) }}</td>
                  <td>{{ formatLatency(getPercentile(item, item.test_type, 'p95')) }}</td>
                  <td>{{ formatLatency(getPercentile(item, item.test_type, 'p99')) }}</td>
                  <td>{{ formatLatency(getPercentile(item, item.test_type, 'p999')) }}</td>
                  <td>{{ formatLatency(getPercentile(item, item.test_type, 'p9999')) }}</td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
        <div v-else class="empty-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
          <p>暂无性能数据</p>
        </div>
      </div>

      <!-- 日志 Tab -->
      <div v-show="activeTab === 'logs'" class="tab-panel">
        <div class="section-header">
          <div class="section-title">
            <h3>执行日志</h3>
            <span class="node-count">共 {{ logs.length }} 条日志</span>
          </div>
          <el-button @click="loadLogs">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
            刷新
          </el-button>
        </div>
        <div class="log-list" v-if="logs.length > 0">
          <div v-for="log in logs" :key="log.id" :class="['log-item', `log-${log.log_level}`]">
            <span class="log-time">{{ formatTime(log.created_at) }}</span>
            <span :class="['log-level', log.log_level]">{{ getLogText(log.log_level) }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
        <div v-else class="empty-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
          <p>暂无日志</p>
        </div>
      </div>
    </div>

    <!-- 添加节点对话框 -->
    <el-dialog v-model="addNodeVisible" title="添加节点" width="600px" class="node-dialog">
      <el-form :model="nodeForm" label-width="100px" class="node-form">
        <el-form-item label="选择节点">
          <el-select v-model="nodeForm.node_id" placeholder="请选择节点" class="w-full" filterable>
            <el-option
              v-for="n in availableNodes"
              :key="n.id"
              :label="n.node_name"
              :value="n.id"
            >
              <div class="node-option">
                <span class="node-option-name">{{ n.node_name }}</span>
                <span class="node-option-host">{{ n.host }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="分区路径">
          <el-input
            v-model="nodeForm.partitions"
            placeholder="可选，多个分区用逗号分隔，如: /data1, /data2, /mnt"
          />
        </el-form-item>
        <div class="form-tip">可选，支持同时添加多个分区，逗号分隔</div>
      </el-form>
      <template #footer>
        <el-button @click="addNodeVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddNode" :disabled="!nodeForm.node_id">确定</el-button>
      </template>
    </el-dialog>

    <!-- 编辑节点分区对话框 -->
    <el-dialog v-model="editNodePartitionsVisible" title="编辑节点分区" width="600px" class="node-dialog">
      <el-form :model="editNodeForm" label-width="100px" class="node-form">
        <el-form-item label="节点">
          <span class="text-white">{{ editNodeForm.node_name }}</span>
        </el-form-item>
        <el-form-item label="分区路径">
          <el-input
            v-model="editNodeForm.partitions"
            placeholder="多个分区用逗号分隔，如: /data1, /data2, /mnt"
          />
        </el-form-item>
        <div class="form-tip">支持同时添加多个分区，逗号分隔</div>
      </el-form>
      <template #footer>
        <el-button @click="editNodePartitionsVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUpdateNodePartitions">确定</el-button>
      </template>
    </el-dialog>

    <!-- 添加/编辑用例对话框 -->
    <el-dialog v-model="addCaseVisible" :title="editingCaseIndex >= 0 ? '编辑用例配置' : '添加用例配置'" width="700px" class="case-dialog">
      <el-form :model="caseForm" label-width="100px" class="case-form">
        <el-form-item label="IO引擎">
          <el-select v-model="caseForm.io_engine" class="w-full">
            <el-option label="libaio" value="libaio" />
            <el-option label="sync" value="sync" />
            <el-option label="nvme" value="nvme" />
            <el-option label="posixaio" value="posixaio" />
            <el-option label="io_uring" value="io_uring" />
          </el-select>
        </el-form-item>
        <el-form-item label="块大小 (多选)">
          <el-select v-model="caseForm.block_sizes" multiple placeholder="选择块大小" class="w-full">
            <el-option label="4K" value="4k" />
            <el-option label="8K" value="8k" />
            <el-option label="16K" value="16k" />
            <el-option label="32K" value="32k" />
            <el-option label="64K" value="64k" />
            <el-option label="128K" value="128k" />
            <el-option label="256K" value="256k" />
            <el-option label="512K" value="512k" />
            <el-option label="1M" value="1M" />
            <el-option label="2M" value="2M" />
            <el-option label="4M" value="4M" />
          </el-select>
        </el-form-item>
        <el-form-item label="IO模式 (多选)">
          <el-select v-model="caseForm.rw_modes" multiple placeholder="选择IO模式" class="w-full">
            <el-option label="顺序读 (read)" value="read" />
            <el-option label="顺序写 (write)" value="write" />
            <el-option label="随机读 (randread)" value="randread" />
            <el-option label="随机写 (randwrite)" value="randwrite" />
            <el-option label="混合读写 (rw)" value="rw" />
            <el-option label="随机混合 (randrw)" value="randrw" />
          </el-select>
        </el-form-item>
        <el-form-item label="队列深度">
          <el-input-number v-model="caseForm.queue_depth" :min="1" :max="256" />
        </el-form-item>
        <el-form-item label="IO大小">
          <el-input v-model="caseForm.io_size" placeholder="如: 1G, 10G" />
        </el-form-item>
        <el-form-item label="运行时长(秒)">
          <el-input-number v-model="caseForm.runtime" :min="1" />
        </el-form-item>
        <el-form-item label="Numjobs">
          <el-input-number v-model="caseForm.numjobs" :min="1" :max="32" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addCaseVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveCase">确定</el-button>
      </template>
    </el-dialog>
  </div>

  <div v-else class="loading">
    <el-skeleton :rows="10" animated />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTasksStore } from '@stores/tasks'
import { nodesAPI } from '@api/nodes'
import { casesAPI } from '@api/cases'
import { tasksAPI } from '@api/tasks'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const tasksStore = useTasksStore()

const taskId = computed(() => route.params.id)
const task = computed(() => tasksStore.currentTask)
const activeTab = ref('info')
const taskNodes = ref([])
const logs = ref([])
const taskCases = ref([])
const percentileData = ref([])

// Tab 配置
const InfoIcon = {
  render: () => h('svg', { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
    h('circle', { cx: 12, cy: 12, r: 10 }),
    h('line', { x1: 12, y1: 16, x2: 12, y2: 12 }),
    h('line', { x1: 12, y1: 8, x2: 12.01, y2: 8 })
  ])
}
const NodeIcon = {
  render: () => h('svg', { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
    h('rect', { x: 2, y: 2, width: 20, height: 8, rx: 2, ry: 2 }),
    h('rect', { x: 2, y: 14, width: 20, height: 8, rx: 2, ry: 2 }),
    h('line', { x1: 6, y1: 6, x2: 6.01, y2: 6 }),
    h('line', { x1: 6, y1: 18, x2: 6.01, y2: 18 })
  ])
}
const CaseIcon = {
  render: () => h('svg', { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
    h('path', { d: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z' }),
    h('polyline', { points: '14 2 14 8 20 8' }),
    h('line', { x1: 16, y1: 13, x2: 8, y2: 13 }),
    h('line', { x1: 16, y1: 17, x2: 8, y2: 17 })
  ])
}
const PercentileIcon = {
  render: () => h('svg', { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
    h('line', { x1: 18, y1: 20, x2: 18, y2: 10 }),
    h('line', { x1: 12, y1: 20, x2: 12, y2: 4 }),
    h('line', { x1: 6, y1: 20, x2: 6, y2: 14 })
  ])
}
const LogIcon = {
  render: () => h('svg', { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
    h('path', { d: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z' }),
    h('polyline', { points: '14 2 14 8 20 8' }),
    h('line', { x1: 16, y1: 13, x2: 8, y2: 13 }),
    h('line', { x1: 16, y1: 17, x2: 8, y2: 17 })
  ])
}

const tabs = computed(() => [
  { key: 'info', label: '基本信息', icon: InfoIcon },
  { key: 'nodes', label: '节点', icon: NodeIcon, count: taskNodes.value.length },
  { key: 'case', label: '用例', icon: CaseIcon, count: taskCases.value.length },
  { key: 'percentiles', label: '性能详情', icon: PercentileIcon, count: percentileData.value.length },
  { key: 'logs', label: '日志', icon: LogIcon, count: logs.value.length }
])

// 添加节点
const addNodeVisible = ref(false)
const availableNodes = ref([])
const nodeForm = ref({ node_id: null, partitions: '' })

// 编辑节点分区
const editNodePartitionsVisible = ref(false)
const editNodeForm = ref({ task_node_id: null, node_id: null, node_name: '', partitions: '' })

// 添加用例
const addCaseVisible = ref(false)
const editingCaseIndex = ref(-1)
const caseForm = ref({
  io_engine: 'libaio',
  block_sizes: ['4k'],
  rw_modes: ['read'],
  queue_depth: 32,
  io_size: '1G',
  runtime: 60,
  numjobs: 1
})

const statusClass = computed(() => ({
  'status-pending': task.value?.status === 'pending',
  'status-running': task.value?.status === 'running',
  'status-completed': task.value?.status === 'completed',
  'status-failed': task.value?.status === 'failed'
}))

const formatTime = (t) => t ? new Date(t).toLocaleString('zh-CN') : '-'
const formatNumber = (n) => n ? new Intl.NumberFormat().format(Math.round(n)) : '0'
const formatBw = (mbs) => mbs ? `${(mbs / 1024).toFixed(2)} GB/s` : '0 GB/s'
const formatLatency = (ms) => ms ? `${ms.toFixed(2)} ms` : '0 ms'
const formatDuration = (s) => {
  if (!s) return '0秒'
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  return h > 0 ? `${h}小时${m}分钟` : `${m}分钟`
}
const formatSize = (bytes) => {
  if (!bytes) return ''
  const gb = bytes / (1024 * 1024 * 1024)
  return gb >= 1 ? `${gb.toFixed(1)} GB` : `${(bytes / (1024 * 1024)).toFixed(0)} MB`
}

const getStatusText = (s) => ({ pending: '待执行', running: '运行中', completed: '已完成', failed: '失败', cancelled: '已取消' }[s] || s)
const getNodeStatusClass = (s) => ({ pending: 'status-pending', running: 'status-running', completed: 'status-completed', failed: 'status-failed' }[s] || 'status-pending')
const getLogText = (l) => ({ info: '信息', warning: '警告', error: '错误', debug: '调试' }[l] || l)
const getRwModeText = (rw) => ({ read: '顺序读', write: '顺序写', randread: '随机读', randwrite: '随机写', rw: '混合读写', randrw: '随机混合' }[rw] || rw)

// 加载任务详情
const loadTask = async () => {
  await tasksStore.fetchTask(taskId.value)
  taskNodes.value = tasksStore.currentTask?.task_nodes || []
  // 从 task.test_case 解析用例配置
  if (tasksStore.currentTask?.test_case) {
    const tc = tasksStore.currentTask.test_case
    taskCases.value = [{
      io_engine: tc.io_engine,
      block_sizes: tc.block_size ? [tc.block_size] : ['4k'],
      rw_modes: tc.rw_mode ? [tc.rw_mode] : ['read'],
      queue_depth: tc.queue_depth,
      io_size: tc.io_size,
      runtime: tc.runtime,
      numjobs: tc.numjobs
    }]
  }
}

// 加载日志
const loadLogs = async () => {
  try {
    const res = await tasksAPI.getTaskLogs(taskId.value)
    logs.value = Array.isArray(res) ? res : (res.data || [])
  } catch (e) {
    console.error('Load logs failed:', e)
  }
}

// 加载百分位数据
const loadPercentiles = async () => {
  try {
    const res = await tasksAPI.getTaskPercentiles(taskId.value)
    percentileData.value = res || []
  } catch (e) {
    console.error('Load percentiles failed:', e)
  }
}

// 获取指定百分位值
const getPercentile = (nodeData, testType, percentileName) => {
  const found = percentileData.value.find(p =>
    p.task_node_id === nodeData.task_node_id &&
    p.test_type === testType &&
    p.percentile_name === percentileName
  )
  return found ? found.latency_us : '-'
}

// 按节点分组百分位数据
const groupedPercentiles = computed(() => {
  const grouped = {}
  percentileData.value.forEach(p => {
    if (!grouped[p.task_node_id]) {
      const taskNode = taskNodes.value.find(tn => tn.id === p.task_node_id)
      grouped[p.task_node_id] = {
        node_id: p.task_node_id,
        node_name: taskNode?.node?.name || `节点 ${p.task_node_id}`,
        data: []
      }
    }
    // 检查是否已添加该 test_type 的数据
    const existingEntry = grouped[p.task_node_id].data.find(d => d.test_type === p.test_type)
    if (existingEntry) {
      // 更新已有的百分位数据
      Object.assign(existingEntry, { [p.percentile_name]: p.latency_us })
    } else {
      // 添加新的百分位数据行
      grouped[p.task_node_id].data.push({
        task_node_id: p.task_node_id,
        test_type: p.test_type,
        [p.percentile_name]: p.latency_us
      })
    }
  })
  return Object.values(grouped)
})

// 加载可用节点
const loadAvailableNodes = async () => {
  try {
    const res = await nodesAPI.getNodes({ limit: 100 })
    availableNodes.value = res || []
  } catch (e) {
    console.error('Load nodes failed:', e)
  }
}

// 显示添加节点对话框
const showAddNodeDialog = async () => {
  nodeForm.value = { node_id: null, partitions: '' }
  await loadAvailableNodes()
  addNodeVisible.value = true
}

// 添加节点
const handleAddNode = async () => {
  if (!nodeForm.value.node_id) {
    ElMessage.warning('请选择节点')
    return
  }
  try {
    // 所有分区一次性发送（逗号分隔）
    await tasksAPI.addTaskNode(taskId.value, {
      node_id: nodeForm.value.node_id,
      partition_path: nodeForm.value.partitions || ''
    })
    ElMessage.success('节点已添加')
    addNodeVisible.value = false
    await loadTask()
  } catch (e) {
    ElMessage.error('添加失败: ' + (e.message || '未知错误'))
  }
}

// 移除节点
const handleRemoveNode = async (node) => {
  try {
    await ElMessageBox.confirm('确定移除该节点？', '确认', { type: 'warning' })
    await tasksAPI.removeTaskNode(taskId.value, node.node_id)
    ElMessage.success('节点已移除')
    await loadTask()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('移除失败')
  }
}

// 编辑节点分区
const handleEditNodePartitions = async (taskNode) => {
  editNodeForm.value = {
    task_node_id: taskNode.id,
    node_id: taskNode.node_id,
    node_name: taskNode.node?.name || `节点 ${taskNode.node_id}`,
    partitions: taskNode.partitions || taskNode.partition?.mount_point || ''
  }
  editNodePartitionsVisible.value = true
}

const handleUpdateNodePartitions = async () => {
  if (!editNodeForm.value.task_node_id) {
    ElMessage.warning('无效的任务节点')
    return
  }
  try {
    // 解析逗号分隔的分区
    const partitionList = editNodeForm.value.partitions
      ? editNodeForm.value.partitions.split(',').map(p => p.trim()).filter(p => p)
      : []

    // 调用 API 更新节点分区
    await tasksAPI.updateTaskNodePartitions(taskId.value, editNodeForm.value.task_node_id, {
      partition_path: partitionList.join(',')
    })

    ElMessage.success('节点分区已更新')
    editNodePartitionsVisible.value = false
    await loadTask()
  } catch (e) {
    ElMessage.error('更新失败: ' + (e.message || '未知错误'))
  }
}

// 显示添加用例对话框
const showAddCaseDialog = () => {
  editingCaseIndex.value = -1
  caseForm.value = {
    io_engine: 'libaio',
    block_sizes: ['4k'],
    rw_modes: ['read'],
    queue_depth: 32,
    io_size: '1G',
    runtime: 60,
    numjobs: 1
  }
  addCaseVisible.value = true
}

// 编辑用例配置
const editCaseConfig = (tc) => {
  editingCaseIndex.value = taskCases.value.indexOf(tc)
  caseForm.value = { ...tc }
  addCaseVisible.value = true
}

// 删除用例配置
const removeCaseConfig = (index) => {
  taskCases.value.splice(index, 1)
  ElMessage.success('用例配置已删除')
}

// 保存用例配置
const handleSaveCase = async () => {
  if (!caseForm.value.block_sizes?.length) {
    ElMessage.warning('请至少选择一个块大小')
    return
  }
  if (!caseForm.value.rw_modes?.length) {
    ElMessage.warning('请至少选择一个IO模式')
    return
  }
  if (editingCaseIndex.value >= 0) {
    taskCases.value[editingCaseIndex.value] = { ...caseForm.value }
    ElMessage.success('用例配置已更新')
  } else {
    taskCases.value.push({ ...caseForm.value })
    ElMessage.success('用例配置已添加')
  }
  addCaseVisible.value = false
}

// 基础操作
const handleStart = async () => {
  try {
    await tasksStore.startTask(taskId.value)
    ElMessage.success('任务启动中...')
    await loadTask() // 刷新任务状态
  } catch (e) {
    ElMessage.error('启动失败: ' + (e.message || '未知错误'))
  }
}
const handleStop = async () => {
  await tasksStore.stopTask(taskId.value)
  ElMessage.success('已停止')
}
const handleDelete = async () => {
  await ElMessageBox.confirm(`确定删除任务 "${task.value.task_name}"？`, '确认', { type: 'warning' })
  await tasksStore.deleteTask(taskId.value)
  router.push('/tasks')
}

onMounted(async () => {
  await loadTask()
  await loadLogs()
  await loadPercentiles()
})

// 切换 Tab 时加载对应数据
watch(activeTab, async (newTab) => {
  if (newTab === 'percentiles' && percentileData.value.length === 0) {
    await loadPercentiles()
  }
})
</script>

<style scoped>
.task-detail { padding: 24px; max-width: 1400px; margin: 0 auto; }

/* 头部 */
.detail-header {
  display: flex;
  align-items: flex-start;
  gap: 24px;
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #334155;
}
.header-left { flex-shrink: 0; }
.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #94a3b8;
  font-size: 14px;
  transition: color 0.2s;
}
.back-btn:hover { color: #fff; }
.header-center { flex: 1; }
.header-center h1 {
  font-size: 28px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 12px 0;
}
.header-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #64748b;
  font-size: 14px;
}
.meta-divider { color: #334155; }
.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}
.status-badge.status-pending { background: rgba(148, 163, 184, 0.2); color: #94a3b8; }
.status-badge.status-running { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }
.status-badge.status-completed { background: rgba(52, 211, 153, 0.2); color: #34d399; }
.status-badge.status-failed { background: rgba(248, 113, 113, 0.2); color: #f87171; }
.header-right {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

/* 指标卡片 */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}
.metric-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 20px;
}
.metric-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.metric-icon.iops { background: rgba(96, 165, 250, 0.15); color: #60a5fa; }
.metric-icon.bw { background: rgba(52, 211, 153, 0.15); color: #34d399; }
.metric-icon.latency { background: rgba(251, 191, 36, 0.15); color: #fbbf24; }
.metric-icon.duration { background: rgba(248, 113, 113, 0.15); color: #f87171; }
.metric-content { flex: 1; }
.metric-value { font-size: 24px; font-weight: 600; color: #fff; }
.metric-label { font-size: 13px; color: #64748b; margin-top: 4px; }

/* Tab 导航 */
.tab-navigation {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  padding: 6px;
  background: #1e293b;
  border-radius: 12px;
  border: 1px solid #334155;
}
.tab-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border: none;
  background: transparent;
  color: #94a3b8;
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.tab-btn:hover { background: #334155; color: #fff; }
.tab-btn.active { background: #3b82f6; color: #fff; }
.tab-count {
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  font-size: 12px;
}
.tab-btn:not(.active) .tab-count { background: #334155; }

/* Tab 内容 */
.tab-content {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 24px;
  min-height: 400px;
}
.tab-panel { animation: fadeIn 0.2s ease; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.section-title { display: flex; align-items: center; gap: 12px; }
.section-title h3 { font-size: 16px; font-weight: 600; color: #fff; margin: 0; }
.node-count { color: #64748b; font-size: 13px; }

/* 信息网格 */
.info-section { margin-bottom: 24px; }
.info-section h3 { font-size: 14px; font-weight: 600; color: #94a3b8; margin: 0 0 16px 0; text-transform: uppercase; letter-spacing: 0.5px; }
.info-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.info-item { display: flex; flex-direction: column; gap: 6px; }
.info-label { font-size: 12px; color: #64748b; }
.info-value { font-size: 14px; color: #fff; font-weight: 500; }
.status-text { font-weight: 600; }
.status-text.status-pending { color: #94a3b8; }
.status-text.status-running { color: #fbbf24; }
.status-text.status-completed { color: #34d399; }
.status-text.status-failed { color: #f87171; }
.description-text { color: #cbd5e1; margin: 0; line-height: 1.6; }

/* 节点表格 */
.node-table { margin-top: 16px; }
.node-info { display: flex; flex-direction: column; gap: 2px; }
.node-name { font-weight: 500; color: #fff; }
.node-host { font-size: 12px; color: #64748b; }
.partition-fs { font-size: 12px; color: #64748b; margin-left: 8px; }
.node-status { font-weight: 500; }
.node-status.status-pending { color: #94a3b8; }
.node-status.status-running { color: #fbbf24; }
.node-status.status-completed { color: #34d399; }
.node-status.status-failed { color: #f87171; }

/* 节点选择对话框 */
.node-form .el-select { width: 100%; }
.node-option { display: flex; justify-content: space-between; width: 100%; }
.node-option-name { font-weight: 500; }
.node-option-host { color: #64748b; font-size: 12px; }
.partition-option { display: flex; justify-content: space-between; width: 100%; }
.partition-size { color: #64748b; font-size: 12px; }
.form-tip { font-size: 12px; color: #64748b; margin-top: 4px; padding-left: 100px; }

/* 用例列表 */
.case-list { display: flex; flex-direction: column; gap: 16px; }
.case-card {
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 8px;
  overflow: hidden;
}
.case-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #1e293b;
  border-bottom: 1px solid #334155;
}
.case-index { font-weight: 600; color: #fff; }
.case-actions { display: flex; gap: 8px; }
.case-card-content { padding: 16px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.case-row { display: flex; flex-direction: column; gap: 6px; }
.case-label { font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }
.case-value { font-size: 14px; color: #fff; font-weight: 500; }
.multi-values { display: flex; flex-wrap: wrap; gap: 6px; }
.value-tag {
  padding: 4px 10px;
  background: #334155;
  border-radius: 4px;
  font-size: 12px;
  color: #fff;
}
.value-tag.mode { background: rgba(59, 130, 246, 0.3); }

/* 用例对话框 */
.case-form .el-select { width: 100%; }
.case-form .el-input-number { width: 100%; }

/* 日志列表 */
.log-list { display: flex; flex-direction: column; gap: 8px; max-height: 500px; overflow-y: auto; }
.log-item {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  background: #0f172a;
  border-radius: 6px;
  font-size: 13px;
  align-items: flex-start;
}
.log-time { color: #64748b; min-width: 160px; font-family: monospace; }
.log-level {
  min-width: 50px;
  padding: 2px 8px;
  border-radius: 4px;
  text-align: center;
  font-weight: 500;
}

/* 百分位表格 */
.percentile-table { overflow-x: auto; }
.percentile-table table { width: 100%; border-collapse: collapse; font-size: 13px; }
.percentile-table th, .percentile-table td {
  padding: 12px 16px;
  text-align: center;
  border: 1px solid #334155;
}
.percentile-table th { background: #1e293b; color: #94a3b8; font-weight: 500; }
.percentile-table td { color: #e2e8f0; }
.percentile-table tr:hover td { background: #1e293b; }
.log-level.info { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
.log-level.warning { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }
.log-level.error { background: rgba(248, 113, 113, 0.2); color: #f87171; }
.log-level.debug { background: rgba(148, 163, 184, 0.2); color: #94a3b8; }
.log-message { color: #cbd5e1; flex: 1; word-break: break-all; }

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #64748b;
}
.empty-state svg { margin-bottom: 16px; opacity: 0.5; }
.empty-state p { margin: 0 0 20px 0; font-size: 14px; }

/* 加载状态 */
.loading { padding: 40px; }

/* 通用样式 */
.w-full { width: 100%; }
</style>
