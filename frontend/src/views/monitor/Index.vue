<template>
  <div class="fade-in">
    <!-- 页面标题 -->
    <div class="page-header">
      <div>
        <h1 class="page-title">实时监控</h1>
        <div class="page-subtitle">实时监控系统性能和 IO 测试数据</div>
      </div>
    </div>

    <!-- 实时数据控制 -->
    <div class="card p-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <el-switch
            v-model="realtimeEnabled"
            active-text="实时监控"
            @change="toggleRealtime"
          />
          <el-select
            v-model="refreshInterval"
            placeholder="刷新间隔"
            class="w-32"
            @change="updateRefreshInterval"
          >
            <el-option label="1秒" :value="1000" />
            <el-option label="2秒" :value="2000" />
            <el-option label="5秒" :value="5000" />
            <el-option label="10秒" :value="10000" />
          </el-select>
        </div>
        <div class="flex items-center space-x-3">
          <el-button
            type="primary"
            @click="refreshAllData"
            :loading="refreshing"
          >
            <ArrowPathIcon class="w-4 h-4 mr-1" />
            刷新数据
          </el-button>
          <el-button
            type="success"
            @click="startRecording"
            v-if="!isRecording"
          >
            <VideoPlay class="w-4 h-4 mr-1" />
            开始录制
          </el-button>
          <el-button
            type="danger"
            @click="stopRecording"
            v-else
          >
            <VideoPause class="w-4 h-4 mr-1" />
            停止录制
          </el-button>
        </div>
      </div>
    </div>

    <!-- 节点分区性能监控 -->
    <div class="card p-4">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-white">节点分区性能监控</h3>
        <el-tag v-if="partitionMonitorId" type="success" size="small">
          监控ID: {{ partitionMonitorId }}
        </el-tag>
      </div>

      <!-- 监控配置 -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
        <el-select
          v-model="selectedNodeId"
          placeholder="选择节点"
          clearable
          @change="onNodeChange"
          :disabled="!!partitionMonitorId"
        >
          <el-option
            v-for="node in onlineNodes"
            :key="node.id"
            :label="node.node_name"
            :value="node.id"
          />
        </el-select>

        <el-select
          v-model="selectedPartitionIds"
          placeholder="选择分区"
          multiple
          collapse-tags
          collapse-tags-tooltip
          :disabled="!!partitionMonitorId || !selectedNodeId"
          class="w-full"
        >
          <el-option
            v-for="partition in availablePartitions"
            :key="partition.id"
            :label="`${partition.partition_name} (${partition.mount_point})`"
            :value="partition.id"
          />
        </el-select>

        <el-input-number
          v-model="monitorInterval"
          :min="1"
          :max="60"
          :disabled="!!partitionMonitorId"
          placeholder="采集间隔(秒)"
        />

        <div class="flex space-x-2">
          <el-button
            type="primary"
            @click="startPartitionMonitor"
            :disabled="!selectedNodeId || selectedPartitionIds.length === 0 || !!partitionMonitorId"
            :loading="startingMonitor"
          >
            开始监控
          </el-button>
          <el-button
            type="danger"
            @click="stopPartitionMonitor"
            :disabled="!partitionMonitorId"
            :loading="stoppingMonitor"
          >
            停止监控
          </el-button>
        </div>
      </div>

      <!-- 监控数据表格 -->
      <div v-if="partitionMonitorId" class="mt-4">
        <el-table
          :data="partitionPerformanceData"
          stripe
          border
          height="300"
          class="w-full"
        >
          <el-table-column prop="timestamp" label="时间" width="180" />
          <el-table-column prop="mount_point" label="挂载点" width="120" />
          <el-table-column prop="device" label="设备" width="100" />
          <el-table-column prop="iops" label="总IOPS" width="100" align="right">
            <template #default="{ row }">
              {{ formatNumber(row.iops) }}
            </template>
          </el-table-column>
          <el-table-column prop="read_iops" label="读IOPS" width="100" align="right">
            <template #default="{ row }">
              {{ formatNumber(row.read_iops) }}
            </template>
          </el-table-column>
          <el-table-column prop="write_iops" label="写IOPS" width="100" align="right">
            <template #default="{ row }">
              {{ formatNumber(row.write_iops) }}
            </template>
          </el-table-column>
          <el-table-column prop="bw_mbs" label="带宽(MB/s)" width="120" align="right">
            <template #default="{ row }">
              {{ (row.bw_mbs || 0).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="latency_ms" label="延迟(ms)" width="100" align="right">
            <template #default="{ row }">
              {{ (row.latency_ms || 0).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="util_percent" label="利用率%" width="100" align="right">
            <template #default="{ row }">
              {{ (row.util_percent || 0).toFixed(2) }}
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-else class="text-center py-8 text-slate-400">
        选择节点和分区后点击"开始监控"
      </div>
    </div>

    <!-- 实时性能指标 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="card p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-slate-400">系统IOPS</p>
            <p class="text-3xl font-bold text-white">{{ formatNumber(systemMetrics.iops) }}</p>
            <div class="flex items-center mt-1">
              <TrendIcon
                :trend="getTrend(systemMetrics.iops, previousSystemMetrics.iops)"
                class="w-4 h-4 mr-1"
              />
              <span class="text-xs text-slate-400">
                {{ getTrendText(systemMetrics.iops, previousSystemMetrics.iops) }}
              </span>
            </div>
          </div>
          <div class="p-3 bg-primary-600/20 rounded-lg">
            <ChartBarIcon class="w-8 h-8 text-primary-400" />
          </div>
        </div>
      </div>

      <div class="card p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-slate-400">系统带宽</p>
            <p class="text-3xl font-bold text-white">{{ formatBytes(systemMetrics.bandwidth) }}/s</p>
            <div class="flex items-center mt-1">
              <TrendIcon
                :trend="getTrend(systemMetrics.bandwidth, previousSystemMetrics.bandwidth)"
                class="w-4 h-4 mr-1"
              />
              <span class="text-xs text-slate-400">
                {{ getTrendText(systemMetrics.bandwidth, previousSystemMetrics.bandwidth) }}
              </span>
            </div>
          </div>
          <div class="p-3 bg-success-600/20 rounded-lg">
            <ArrowDownTrayIcon class="w-8 h-8 text-success-400" />
          </div>
        </div>
      </div>

      <div class="card p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-slate-400">平均延迟</p>
            <p class="text-3xl font-bold text-white">{{ formatLatency(systemMetrics.latency) }}</p>
            <div class="flex items-center mt-1">
              <TrendIcon
                :trend="getTrend(systemMetrics.latency, previousSystemMetrics.latency, true)"
                class="w-4 h-4 mr-1"
              />
              <span class="text-xs text-slate-400">
                {{ getTrendText(systemMetrics.latency, previousSystemMetrics.latency, true) }}
              </span>
            </div>
          </div>
          <div class="p-3 bg-warning-600/20 rounded-lg">
            <ClockIcon class="w-8 h-8 text-warning-400" />
          </div>
        </div>
      </div>

      <div class="card p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-slate-400">CPU使用率</p>
            <p class="text-3xl font-bold text-white">{{ formatPercent(systemMetrics.cpu_usage) }}</p>
            <div class="flex items-center mt-1">
              <TrendIcon
                :trend="getTrend(systemMetrics.cpu_usage, previousSystemMetrics.cpu_usage)"
                class="w-4 h-4 mr-1"
              />
              <span class="text-xs text-slate-400">
                {{ getTrendText(systemMetrics.cpu_usage, previousSystemMetrics.cpu_usage) }}
              </span>
            </div>
          </div>
          <div class="p-3 bg-info-600/20 rounded-lg">
            <CpuChipIcon class="w-8 h-8 text-info-400" />
          </div>
        </div>
      </div>
    </div>

    <!-- 性能图表 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- IOPS趋势图 -->
      <div class="card p-4">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-white">IOPS趋势</h3>
          <div class="flex items-center space-x-2">
            <el-button
              type="text"
              size="small"
              @click="toggleChartType('iops')"
            >
              {{ chartTypes.iops === 'line' ? '柱状图' : '折线图' }}
            </el-button>
            <el-select
              v-model="chartTimeRanges.iops"
              size="small"
              class="w-24"
            >
              <el-option label="5分钟" :value="5" />
              <el-option label="15分钟" :value="15" />
              <el-option label="30分钟" :value="30" />
              <el-option label="1小时" :value="60" />
            </el-select>
          </div>
        </div>
        <div ref="iopsChart" class="h-64"></div>
      </div>

      <!-- 带宽趋势图 -->
      <div class="card p-4">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-white">带宽趋势</h3>
          <div class="flex items-center space-x-2">
            <el-button
              type="text"
              size="small"
              @click="toggleChartType('bandwidth')"
            >
              {{ chartTypes.bandwidth === 'line' ? '柱状图' : '折线图' }}
            </el-button>
            <el-select
              v-model="chartTimeRanges.bandwidth"
              size="small"
              class="w-24"
            >
              <el-option label="5分钟" :value="5" />
              <el-option label="15分钟" :value="15" />
              <el-option label="30分钟" :value="30" />
              <el-option label="1小时" :value="60" />
            </el-select>
          </div>
        </div>
        <div ref="bandwidthChart" class="h-64"></div>
      </div>

      <!-- 延迟分布图 -->
      <div class="card p-4">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-white">延迟分布</h3>
          <el-select
            v-model="chartTimeRanges.latency"
            size="small"
            class="w-24"
          >
            <el-option label="5分钟" :value="5" />
            <el-option label="15分钟" :value="15" />
            <el-option label="30分钟" :value="30" />
            <el-option label="1小时" :value="60" />
          </el-select>
        </div>
        <div ref="latencyChart" class="h-64"></div>
      </div>

      <!-- CPU使用率图 -->
      <div class="card p-4">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-white">CPU使用率</h3>
          <el-select
            v-model="chartTimeRanges.cpu"
            size="small"
            class="w-24"
          >
            <el-option label="5分钟" :value="5" />
            <el-option label="15分钟" :value="15" />
            <el-option label="30分钟" :value="30" />
            <el-option label="1小时" :value="60" />
          </el-select>
        </div>
        <div ref="cpuChart" class="h-64"></div>
      </div>
    </div>

    <!-- 运行任务监控 -->
    <div class="card p-4">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-white">运行任务监控</h3>
        <el-button
          type="text"
          @click="expandAllTasks = !expandAllTasks"
        >
          {{ expandAllTasks ? '收起全部' : '展开全部' }}
        </el-button>
      </div>
      
      <div v-if="runningTasks.length > 0" class="space-y-4">
        <div
          v-for="task in runningTasks"
          :key="task.id"
          class="border border-slate-700/50 rounded-lg p-4"
        >
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center">
              <div class="w-3 h-3 bg-success-500 rounded-full mr-3 animate-pulse"></div>
              <h4 class="text-white font-medium">{{ task.name }}</h4>
            </div>
            <div class="flex items-center space-x-2">
              <span class="text-sm text-slate-400">{{ task.node_name }}</span>
              <button
                @click="toggleTaskExpansion(task.id)"
                class="p-1 rounded hover:bg-slate-700/50"
              >
                <ChevronDownIcon
                  :class="['w-4 h-4 text-slate-400 transition-transform', expandedTasks.includes(task.id) ? 'rotate-180' : '']"
                />
              </button>
            </div>
          </div>
          
          <div class="mb-3">
            <el-progress
              :percentage="task.progress || 0"
              :status="task.progress === 100 ? 'success' : ''"
              :stroke-width="6"
            />
            <div class="flex justify-between text-xs text-slate-400 mt-1">
              <span>进度: {{ task.progress || 0 }}%</span>
              <span>预计剩余: {{ formatDuration(task.eta || 0) }}</span>
            </div>
          </div>
          
          <div v-if="expandedTasks.includes(task.id)" class="grid grid-cols-1 md:grid-cols-4 gap-4 pt-4 border-t border-slate-700/50">
            <div class="text-center">
              <div class="text-xl font-bold text-white">{{ formatNumber(taskMetrics[task.id]?.iops || 0) }}</div>
              <div class="text-xs text-slate-400">IOPS</div>
            </div>
            <div class="text-center">
              <div class="text-xl font-bold text-white">{{ formatBytes(taskMetrics[task.id]?.bandwidth || 0) }}/s</div>
              <div class="text-xs text-slate-400">带宽</div>
            </div>
            <div class="text-center">
              <div class="text-xl font-bold text-white">{{ formatLatency(taskMetrics[task.id]?.latency || 0) }}</div>
              <div class="text-xs text-slate-400">延迟</div>
            </div>
            <div class="text-center">
              <div class="text-xl font-bold text-white">{{ formatPercent(taskMetrics[task.id]?.cpu_usage || 0) }}</div>
              <div class="text-xs text-slate-400">CPU</div>
            </div>
          </div>
        </div>
      </div>
      
      <div v-else class="text-center py-8">
        <PlayIcon class="w-12 h-12 text-slate-600 mx-auto mb-2" />
        <p class="text-slate-400">暂无运行中的任务</p>
      </div>
    </div>

    <!-- 历史数据 -->
    <div class="card p-4">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-white">历史性能数据</h3>
        <div class="flex items-center space-x-2">
          <el-date-picker
            v-model="historyDateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            size="small"
            class="w-80"
          />
          <el-button
            type="primary"
            size="small"
            @click="loadHistoryData"
          >
            加载数据
          </el-button>
        </div>
      </div>
      
      <div ref="historyChart" class="h-80"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import axios from 'axios'
import { useTasksStore } from '@stores/tasks'
import { useMonitorStore } from '@stores/monitor'
import { useNodesStore } from '@stores/nodes'
import { useWebSocketStore } from '@stores/websocket'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import {
  ArrowPathIcon,
  ChartBarIcon,
  ArrowDownTrayIcon,
  ClockIcon,
  CpuChipIcon,
  PlayIcon
} from '@heroicons/vue/24/outline'
import { ChevronDownIcon } from '@heroicons/vue/24/solid'
import { partitionMonitorAPI } from './api'
import { nodesAPI } from '@api/nodes'

const tasksStore = useTasksStore()
const monitorStore = useMonitorStore()
const nodesStore = useNodesStore()
const wsStore = useWebSocketStore()

// 状态
const realtimeEnabled = ref(false)
const refreshInterval = ref(5000)
const refreshing = ref(false)
const isRecording = ref(false)
const expandAllTasks = ref(false)
const expandedTasks = ref([])
const historyDateRange = ref([])

// 节点分区监控状态
const selectedNodeId = ref(null)
const selectedPartitionIds = ref([])
const availablePartitions = ref([])
const monitorInterval = ref(1)
const partitionMonitorId = ref(null)
const partitionPerformanceData = ref([])
const startingMonitor = ref(false)
const stoppingMonitor = ref(false)

// 计算属性
const onlineNodes = computed(() => nodesStore.onlineNodes)
const runningTasks = computed(() => tasksStore.runningTasks)

// WebSocket 连接
let partitionWs = null

// 图表实例
let chartInstances = {}

// 格式化数字
const formatNumber = (num) => {
  return new Intl.NumberFormat('zh-CN').format(Math.round(num))
}

// 格式化字节
const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B'
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}

// 格式化延迟
const formatLatency = (microseconds) => {
  if (microseconds < 1000) {
    return Math.round(microseconds) + ' μs'
  } else if (microseconds < 1000000) {
    return Math.round(microseconds / 1000 * 100) / 100 + ' ms'
  } else {
    return Math.round(microseconds / 1000000 * 100) / 100 + ' s'
  }
}

// 格式化百分比
const formatPercent = (value) => {
  return Math.round(value * 100) / 100 + '%'
}

// 格式化时长
const formatDuration = (seconds) => {
  if (!seconds) return '0s'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`
  } else {
    return `${secs}s`
  }
}

// 获取趋势
const getTrend = (current, previous, inverse = false) => {
  if (current > previous) {
    return inverse ? 'down' : 'up'
  } else if (current < previous) {
    return inverse ? 'up' : 'down'
  } else {
    return 'stable'
  }
}

// 获取趋势文本
const getTrendText = (current, previous, inverse = false) => {
  const trend = getTrend(current, previous, inverse)
  const diff = Math.abs(current - previous)
  
  switch (trend) {
    case 'up':
      return inverse ? `↓ ${formatNumber(diff)}` : `↑ ${formatNumber(diff)}`
    case 'down':
      return inverse ? `↑ ${formatNumber(diff)}` : `↓ ${formatNumber(diff)}`
    default:
      return '稳定'
  }
}

// 切换图表类型
const toggleChartType = (chartName) => {
  chartTypes.value[chartName] = chartTypes.value[chartName] === 'line' ? 'bar' : 'line'
  updateChart(chartName)
}

// 切换任务展开状态
const toggleTaskExpansion = (taskId) => {
  const index = expandedTasks.value.indexOf(taskId)
  if (index > -1) {
    expandedTasks.value.splice(index, 1)
  } else {
    expandedTasks.value.push(taskId)
  }
}

// 初始化图表
const initCharts = () => {
  // IOPS图表
  chartInstances.iops = echarts.init(iopsChart.value)
  chartInstances.iops.setOption({
    backgroundColor: 'transparent',
    grid: { top: 20, right: 20, bottom: 40, left: 60 },
    xAxis: {
      type: 'category',
      data: [],
      axisLine: { lineStyle: { color: '#475569' } },
      axisLabel: { color: '#94a3b8' }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#475569' } },
      axisLabel: { color: '#94a3b8' },
      splitLine: { lineStyle: { color: '#334155' } }
    },
    series: [{
      data: [],
      type: 'line',
      smooth: true,
      lineStyle: { color: '#3b82f6' },
      itemStyle: { color: '#3b82f6' },
      areaStyle: { color: 'rgba(59, 130, 246, 0.1)' }
    }]
  })

  // 带宽图表
  chartInstances.bandwidth = echarts.init(bandwidthChart.value)
  chartInstances.bandwidth.setOption({
    backgroundColor: 'transparent',
    grid: { top: 20, right: 20, bottom: 40, left: 60 },
    xAxis: {
      type: 'category',
      data: [],
      axisLine: { lineStyle: { color: '#475569' } },
      axisLabel: { color: '#94a3b8' }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#475569' } },
      axisLabel: { 
        color: '#94a3b8',
        formatter: (value) => formatBytes(value) + '/s'
      },
      splitLine: { lineStyle: { color: '#334155' } }
    },
    series: [{
      data: [],
      type: 'line',
      smooth: true,
      lineStyle: { color: '#10b981' },
      itemStyle: { color: '#10b981' },
      areaStyle: { color: 'rgba(16, 185, 129, 0.1)' }
    }]
  })

  // 延迟图表
  chartInstances.latency = echarts.init(latencyChart.value)
  chartInstances.latency.setOption({
    backgroundColor: 'transparent',
    grid: { top: 20, right: 20, bottom: 40, left: 60 },
    xAxis: {
      type: 'category',
      data: [],
      axisLine: { lineStyle: { color: '#475569' } },
      axisLabel: { color: '#94a3b8' }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#475569' } },
      axisLabel: { 
        color: '#94a3b8',
        formatter: (value) => formatLatency(value)
      },
      splitLine: { lineStyle: { color: '#334155' } }
    },
    series: [{
      data: [],
      type: 'line',
      smooth: true,
      lineStyle: { color: '#f59e0b' },
      itemStyle: { color: '#f59e0b' },
      areaStyle: { color: 'rgba(245, 158, 11, 0.1)' }
    }]
  })

  // CPU使用率图表
  chartInstances.cpu = echarts.init(cpuChart.value)
  chartInstances.cpu.setOption({
    backgroundColor: 'transparent',
    grid: { top: 20, right: 20, bottom: 40, left: 60 },
    xAxis: {
      type: 'category',
      data: [],
      axisLine: { lineStyle: { color: '#475569' } },
      axisLabel: { color: '#94a3b8' }
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLine: { lineStyle: { color: '#475569' } },
      axisLabel: { 
        color: '#94a3b8',
        formatter: '{value}%'
      },
      splitLine: { lineStyle: { color: '#334155' } }
    },
    series: [{
      data: [],
      type: 'line',
      smooth: true,
      lineStyle: { color: '#6366f1' },
      itemStyle: { color: '#6366f1' },
      areaStyle: { color: 'rgba(99, 102, 241, 0.1)' }
    }]
  })
}

// ===== 图表历史缓存 =====
// 修复：原来 updateChart 每次都生成 20 条 Math.random() 数据画假图。
// 改为维护真实历史缓存，每次刷新追加一个新数据点。
const MAX_CHART_POINTS = 60
const chartHistory = {
  iops: [],        // { ts, v }
  bandwidth: [],
  latency: [],
  cpu: [],
}

const pushChartPoint = (name, value) => {
  const arr = chartHistory[name]
  if (!arr) return
  arr.push({ ts: Date.now(), v: Number(value) || 0 })
  if (arr.length > MAX_CHART_POINTS) {
    arr.splice(0, arr.length - MAX_CHART_POINTS)
  }
}

// 更新图表 —— 基于真实历史数据重绘
const updateChart = (chartName) => {
  const inst = chartInstances[chartName]
  if (!inst) return
  const arr = chartHistory[chartName] || []
  const timestamps = arr.map(p =>
    new Date(p.ts).toLocaleTimeString('zh-CN', { hour12: false })
  )
  const values = arr.map(p => p.v)
  inst.setOption({
    xAxis: { data: timestamps },
    series: [{ data: values }],
  })
}

// 刷新所有数据 —— 改为真实从后端拉取
const refreshAllData = async () => {
  refreshing.value = true
  try {
    // 保存之前的指标用于趋势计算
    previousSystemMetrics.value = { ...systemMetrics.value }

    // 1) 拉取系统级采样（沿用后端 /api/monitor/sample 接口）
    let sample = null
    try {
      const { data } = await axios.get('/api/monitor/sample')
      sample = data || null
    } catch (err) {
      console.warn('[monitor] fetch sample failed:', err?.message)
    }

    if (sample) {
      // 注意：/monitor/sample 返回的是宿主侧 CPU/mem/disk，IOPS/带宽/延迟
      // 属于任务级指标，这里放 0，让任务级数据覆盖
      systemMetrics.value = {
        iops: Number(systemMetrics.value?.iops) || 0,
        bandwidth: Number(systemMetrics.value?.bandwidth) || 0,
        latency: Number(systemMetrics.value?.latency) || 0,
        cpu_usage: Number(sample.cpu) || 0,
      }
    }

    // 2) 获取运行中任务的最新指标
    // 如果上游 store 提供了 fetch 方法，可替换下面这段
    try {
      const tasks = Array.isArray(runningTasks.value) ? runningTasks.value : []
      for (const task of tasks) {
        const { data: metrics } = await axios.get(
          `/api/tasks/${task.id}/metrics`,
          { params: { limit: 1 } }
        ).catch(() => ({ data: null }))
        const latest = Array.isArray(metrics) ? metrics[metrics.length - 1] : null
        if (latest) {
          taskMetrics.value[task.id] = {
            iops: Number(latest.iops) || 0,
            bandwidth: Number(latest.bandwidth) || 0,
            latency: Number(latest.latency) || 0,
            cpu_usage: Number(latest.cpu_usage) || 0,
          }
        }
      }
    } catch (err) {
      console.warn('[monitor] fetch task metrics failed:', err?.message)
    }

    // 3) 把当前最新值追加进各图表历史
    pushChartPoint('iops', systemMetrics.value.iops)
    pushChartPoint('bandwidth', systemMetrics.value.bandwidth)
    pushChartPoint('latency', systemMetrics.value.latency)
    pushChartPoint('cpu', systemMetrics.value.cpu_usage)

    // 4) 更新图表
    Object.keys(chartInstances).forEach(chartName => {
      updateChart(chartName)
    })
  } catch (error) {
    console.error('Refresh error:', error)
  } finally {
    refreshing.value = false
  }
}

// 切换实时监控
const toggleRealtime = () => {
  if (realtimeEnabled.value) {
    monitorStore.startRealtimeMonitoring(refreshInterval.value)
  } else {
    monitorStore.stopRealtimeMonitoring()
  }
}

// 更新刷新间隔
const updateRefreshInterval = () => {
  if (realtimeEnabled.value) {
    monitorStore.setRefreshInterval(refreshInterval.value)
  }
}

// 开始录制
const startRecording = () => {
  isRecording.value = true
  monitorStore.startRecording()
  ElMessage.success('开始录制性能数据')
}

// 停止录制
const stopRecording = () => {
  isRecording.value = false
  monitorStore.stopRecording()
  ElMessage.success('停止录制性能数据')
}

// 加载历史数据
const loadHistoryData = () => {
  // 这里应该根据时间范围加载历史数据
  ElMessage.success('历史数据加载成功')
}

// 节点分区监控方法
const onNodeChange = async (nodeId) => {
  selectedPartitionIds.value = []
  availablePartitions.value = []

  if (nodeId) {
    try {
      const partitions = await nodesAPI.getNodePartitions(nodeId)
      availablePartitions.value = partitions || []
    } catch (error) {
      console.error('Failed to fetch partitions:', error)
      ElMessage.error('获取分区列表失败')
    }
  }
}

const startPartitionMonitor = async () => {
  if (!selectedNodeId.value || selectedPartitionIds.value.length === 0) {
    ElMessage.warning('请选择节点和分区')
    return
  }

  startingMonitor.value = true
  try {
    const response = await partitionMonitorAPI.startMonitor({
      node_id: selectedNodeId.value,
      partition_ids: selectedPartitionIds.value,
      interval: monitorInterval.value
    })

    partitionMonitorId.value = response.monitor_id

    // 连接 WebSocket
    connectPartitionWebSocket(response.monitor_id)

    ElMessage.success('分区监控已启动')
  } catch (error) {
    console.error('Failed to start partition monitor:', error)
    ElMessage.error(error.response?.data?.detail || '启动监控失败')
  } finally {
    startingMonitor.value = false
  }
}

const stopPartitionMonitor = async () => {
  if (!partitionMonitorId.value) return

  stoppingMonitor.value = true
  try {
    await partitionMonitorAPI.stopMonitor(partitionMonitorId.value)

    // 断开 WebSocket
    if (partitionWs) {
      partitionWs.disconnect()
      partitionWs = null
    }

    partitionMonitorId.value = null
    partitionPerformanceData.value = []

    ElMessage.success('分区监控已停止')
  } catch (error) {
    console.error('Failed to stop partition monitor:', error)
    ElMessage.error(error.response?.data?.detail || '停止监控失败')
  } finally {
    stoppingMonitor.value = false
  }
}

const connectPartitionWebSocket = (monitorId) => {
  // 使用已有的 websocket store
  if (!wsStore.socket) {
    ElMessage.error('WebSocket未连接')
    return
  }

  partitionWs = wsStore.socket

  // 监听分区性能数据
  wsStore.socket.on('partition_performance_data', (data) => {
    // 添加到数据列表
    partitionPerformanceData.value.unshift(data)
    // 保留最近100条数据
    if (partitionPerformanceData.value.length > 100) {
      partitionPerformanceData.value.pop()
    }
  })

  // 加入监控房间
  wsStore.socket.emit('join_node_partition_monitor', { monitor_id: monitorId })
}

// resize 回调：容器尺寸变化时让所有图表自适应
const handleMonitorResize = () => {
  Object.values(chartInstances).forEach(chart => {
    if (chart && !chart.isDisposed?.()) {
      chart.resize()
    }
  })
}

// 初始化
onMounted(async () => {
  // 修复：原代码 nextTick 内同步调用 refreshAllData，但 refreshAllData 是 async，
  // 且后面的 await nodesStore.fetchNodes() 与它并发执行，会导致首屏图表可能还没拿到数据
  await nextTick()
  initCharts()

  // 获取节点列表
  try {
    await nodesStore.fetchNodes()
  } catch (err) {
    console.warn('[monitor] fetchNodes failed:', err?.message)
  }

  // 首次刷新（拉真实数据）
  await refreshAllData()

  // 监听 window resize，让图表自适应
  window.addEventListener('resize', handleMonitorResize)

  // 如果启用了实时监控，开始定时刷新
  if (realtimeEnabled.value) {
    toggleRealtime()
  }
})

// 清理
onUnmounted(() => {
  if (realtimeEnabled.value) {
    monitorStore.stopRealtimeMonitoring()
  }

  // 停止分区监控
  if (partitionMonitorId.value) {
    partitionMonitorAPI.stopMonitor(partitionMonitorId.value).catch(() => {})
  }

  // 移除分区性能数据监听
  if (wsStore.socket) {
    wsStore.socket.off('partition_performance_data')
  }
  partitionWs = null

  // 移除 resize 监听
  window.removeEventListener('resize', handleMonitorResize)

  // 销毁图表实例
  Object.values(chartInstances).forEach(chart => {
    if (chart && !chart.isDisposed?.()) {
      chart.dispose()
    }
  })
  chartInstances = {}
})
</script>

<style scoped>
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