<template>
 <el-dialog
 v-model="visible"
 :title="`性能数据 - ${task?.name || '未知任务'}`"
 width="1200px"
 class="metrics-dialog"
 @close="handleClose"
  :destroy-on-close="true"
 >
 <div class="space-y-6">
 <!-- 实时数据开关 -->
 <div class="flex items-center justify-between">
 <h3 class="text-lg font-semibold ">实时性能数据</h3>
 <div class="flex items-center space-x-3">
 <el-switch
 v-model="realtimeEnabled"
 active-text="实时更新"
 @change="toggleRealtime"
 />
 <el-button
 type="primary"
 size="small"
 @click="refreshMetrics"
 :loading="refreshing"
 >
 <ArrowPathIcon class="w-4 h-4 mr-1" />
 刷新
 </el-button>
 </div>
 </div>

 <!-- 性能指标卡片 -->
 <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
 <div class="card p-4">
 <div class="flex items-center justify-between">
 <div>
 <p class="text-sm font-medium text-muted">IOPS</p>
 <p class="text-2xl font-bold ">{{ formatNumber(currentMetrics.iops || 0) }}</p>
 </div>
 <div class="p-2 bg-primary-600/20 rounded-lg">
 <ChartBarIcon class="w-6 h-6 text-primary-400" />
 </div>
 </div>
 <div class="mt-2">
 <span class="text-xs text-muted">
 峰值: {{ formatNumber(peakMetrics.iops || 0) }}
 </span>
 </div>
 </div>

 <div class="card p-4">
 <div class="flex items-center justify-between">
 <div>
 <p class="text-sm font-medium text-muted">带宽</p>
 <p class="text-2xl font-bold ">{{ formatMBps(currentMetrics.bandwidth || 0) }}</p>
 </div>
 <div class="p-2 bg-success-600/20 rounded-lg">
 <ArrowDownTrayIcon class="w-6 h-6 text-success-400" />
 </div>
 </div>
 <div class="mt-2">
 <span class="text-xs text-muted">
 峰值: {{ formatMBps(peakMetrics.bandwidth || 0) }}
 </span>
 </div>
 </div>

 <div class="card p-4">
 <div class="flex items-center justify-between">
 <div>
 <p class="text-sm font-medium text-muted">延迟</p>
 <p class="text-2xl font-bold ">{{ formatLatency(currentMetrics.latency || 0) }}</p>
 </div>
 <div class="p-2 bg-warning-600/20 rounded-lg">
 <ClockIcon class="w-6 h-6 text-warning-400" />
 </div>
 </div>
 <div class="mt-2">
 <span class="text-xs text-muted">
 最低: {{ formatLatency(minMetrics.latency || 0) }}
 </span>
 </div>
 </div>

 <div class="card p-4">
 <div class="flex items-center justify-between">
 <div>
 <p class="text-sm font-medium text-muted">CPU使用率</p>
 <p class="text-2xl font-bold ">{{ formatPercent(currentMetrics.cpu_usage || 0) }}</p>
 </div>
 <div class="p-2 bg-info-600/20 rounded-lg">
 <CpuChipIcon class="w-6 h-6 text-info-400" />
 </div>
 </div>
 <div class="mt-2">
 <span class="text-xs text-muted">
 平均: {{ formatPercent(avgMetrics.cpu_usage || 0) }}
 </span>
 </div>
 </div>
 </div>

 <!-- 性能图表 -->
 <div class="space-y-3">
 <!-- 时间窗格控制条 -->
 <div class="card p-3 flex items-center justify-between flex-wrap gap-2">
 <div class="flex items-center gap-2 flex-wrap">
 <span class="text-muted text-sm mr-1">时间窗格:</span>
 <el-button-group>
 <el-button
 v-for="opt in rangeOptions"
 :key="opt.value"
 size="small"
 :type="selectedRange === opt.value ? 'primary' : ''"
 @click="applyQuickRange(opt.value)"
 >
 {{ opt.label }}
 </el-button>
 </el-button-group>
 <span class="text-xs text-muted ml-3">
 <template v-if="viewWindow.from && viewWindow.to">
 {{ formatTimeLabel(viewWindow.from) }} ~ {{ formatTimeLabel(viewWindow.to) }}
 </template>
 <template v-else>
 共 {{ metricsHistory.length }} 个采样点
 </template>
 </span>
 </div>
 <div class="flex items-center gap-2">
 <el-tag v-if="!followLatest" type="warning" size="small" effect="dark">
 已锁定时间窗格 · 不跟随实时
 </el-tag>
 <el-tag v-else type="success" size="small" effect="dark">
 跟随最新数据
 </el-tag>
 <el-button
 v-if="!followLatest"
 size="small"
 type="primary"
 @click="resumeFollowLatest"
 >
 回到实时
 </el-button>
 </div>
 </div>

 <!-- 抖动图表区 -->
 <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
 <!-- IOPS图表 -->
 <div class="card p-4">
 <h4 class="font-medium mb-4">IOPS 抖动</h4>
 <div ref="iopsChart" class="h-80"></div>
 </div>

 <!-- 带宽图表 -->
 <div class="card p-4">
 <h4 class="font-medium mb-4">带宽抖动</h4>
 <div ref="bandwidthChart" class="h-80"></div>
 </div>

 <!-- 延迟图表 -->
 <div class="card p-4">
 <h4 class="font-medium mb-4">延迟抖动</h4>
 <div ref="latencyChart" class="h-80"></div>
 </div>

 <!-- CPU使用率图表 -->
 <div class="card p-4">
 <h4 class="font-medium mb-4">CPU 抖动</h4>
 <div ref="cpuChart" class="h-80"></div>
 </div>
 </div>

 <p class="text-xs text-subtle px-1">
 提示：拖动任一图表下方的时间滑块可查看指定时间区间；鼠标滚轮可缩放；四张图已联动。
 </p>
 </div>

 <!-- 性能统计 -->
 <div class="card p-6">
 <h4 class="font-medium mb-4">性能统计</h4>
 <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
 <div class="space-y-3">
 <h5 class="text-muted font-medium">IOPS统计</h5>
 <div class="space-y-2 text-sm">
 <div class="flex justify-between">
 <span class="text-muted">平均值:</span>
 <span class="">{{ formatNumber(avgMetrics.iops || 0) }}</span>
 </div>
 <div class="flex justify-between">
 <span class="text-muted">最大值:</span>
 <span class="">{{ formatNumber(peakMetrics.iops || 0) }}</span>
 </div>
 <div class="flex justify-between">
 <span class="text-muted">最小值:</span>
 <span class="">{{ formatNumber(minMetrics.iops || 0) }}</span>
 </div>
 <div class="flex justify-between">
 <span class="text-muted">标准差:</span>
 <span class="">{{ formatNumber(stdMetrics.iops || 0) }}</span>
 </div>
 </div>
 </div>

 <div class="space-y-3">
 <h5 class="text-muted font-medium">带宽统计</h5>
 <div class="space-y-2 text-sm">
 <div class="flex justify-between">
 <span class="text-muted">平均值:</span>
 <span class="">{{ formatMBps(avgMetrics.bandwidth || 0) }}</span>
 </div>
 <div class="flex justify-between">
 <span class="text-muted">最大值:</span>
 <span class="">{{ formatMBps(peakMetrics.bandwidth || 0) }}</span>
 </div>
 <div class="flex justify-between">
 <span class="text-muted">最小值:</span>
 <span class="">{{ formatMBps(minMetrics.bandwidth || 0) }}</span>
 </div>
 <div class="flex justify-between">
 <span class="text-muted">标准差:</span>
 <span class="">{{ formatMBps(stdMetrics.bandwidth || 0) }}</span>
 </div>
 </div>
 </div>

 <div class="space-y-3">
 <h5 class="text-muted font-medium">延迟统计</h5>
 <div class="space-y-2 text-sm">
 <div class="flex justify-between">
 <span class="text-muted">平均值:</span>
 <span class="">{{ formatLatency(avgMetrics.latency || 0) }}</span>
 </div>
 <div class="flex justify-between">
 <span class="text-muted">最大值:</span>
 <span class="">{{ formatLatency(peakMetrics.latency || 0) }}</span>
 </div>
 <div class="flex justify-between">
 <span class="text-muted">最小值:</span>
 <span class="">{{ formatLatency(minMetrics.latency || 0) }}</span>
 </div>
 <div class="flex justify-between">
 <span class="text-muted">P95:</span>
 <span class="">{{ formatLatency(p95Metrics.latency || 0) }}</span>
 </div>
 </div>
 </div>
 </div>
 </div>
 </div>

 <template #footer>
 <div class="flex justify-end space-x-3">
 <el-button @click="handleClose">关闭</el-button>
 </div>
 </template>
 </el-dialog>
</template>

<script setup>
// ========== BUG 修复 ==========
// 1. 原代码在 onMounted 内用 nextTick() 但未导入，打开对话框即崩溃
// 2. updateCharts 只实现了 IOPS 一张图，其余三张永远空白
// 3. updateStatistics 把 current 同时当作 peak/min/avg/std/p95，全部相等
// 4. updateMetricsData 用 Math.random() 造假数据，不接后端
// 5. onUnmounted 未清除 realtimeTimer 可能的重复残留
// 6. 没有 resize 监听，窗口变化图表不会自适应
// 7. formatBytes 对 bandwidth 0 的处理导致 Math.log(0) = -Infinity
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import {
 ArrowPathIcon,
 ChartBarIcon,
 ArrowDownTrayIcon,
 ClockIcon,
 CpuChipIcon
} from '@heroicons/vue/24/outline'

const props = defineProps({
 modelValue: {
 type: Boolean,
 default: false
 },
 task: {
 type: Object,
 default: null
 },
 metrics: {
 type: Array,
 default: () => []
 }
})

const emit = defineEmits(['update:modelValue', 'close'])

// 状态
const refreshing = ref(false)
const realtimeEnabled = ref(false)
const realtimeTimer = ref(null)

// 图表实例
const iopsChart = ref(null)
const bandwidthChart = ref(null)
const latencyChart = ref(null)
const cpuChart = ref(null)

let chartInstances = {}

// 当前性能数据
const currentMetrics = ref({
 iops: 0,
 bandwidth: 0,
 latency: 0,
 cpu_usage: 0
})

// 统计数据
const peakMetrics = ref({ iops: 0, bandwidth: 0, latency: 0, cpu_usage: 0 })
const minMetrics = ref({ iops: 0, bandwidth: 0, latency: 0, cpu_usage: 0 })
const avgMetrics = ref({ iops: 0, bandwidth: 0, latency: 0, cpu_usage: 0 })
const stdMetrics = ref({ iops: 0, bandwidth: 0, latency: 0, cpu_usage: 0 })
const p95Metrics = ref({ iops: 0, bandwidth: 0, latency: 0, cpu_usage: 0 })

// 新增：真实的数据历史缓存，用于画图和统计（而不是随机数）
// 扩容到 600 点，按默认 2s 一次采样，可覆盖 20 分钟。实时开启时用户能在长窗口里滑动查看抖动。
const MAX_HISTORY = 600
const metricsHistory = ref([]) // [{ timestamp, iops, bandwidth, latency, cpu_usage }]

// ===== 时间窗格（time-window）滑动查看状态 =====
// followLatest: true 时，每次新数据到来图表自动跟到最新；false 表示用户正在手动查看历史
// viewWindow: 当前用户可见的时间范围（毫秒时间戳），null 表示全量
// _zoomProgramming: 内部标记，dataZoom 事件如果是代码触发的，不把 followLatest 翻成 false
const followLatest = ref(true)
const viewWindow = ref({ from: null, to: null })
let _zoomProgramming = false
const selectedRange = ref('all') // 当前选中的快捷范围
const rangeOptions = [
 { label: '最近 1 分钟', value: '1m', seconds: 60 },
 { label: '最近 5 分钟', value: '5m', seconds: 300 },
 { label: '最近 15 分钟', value: '15m', seconds: 900 },
 { label: '最近 1 小时', value: '1h', seconds: 3600 },
 { label: '全部', value: 'all', seconds: null },
]

// 对话框可见性
const visible = computed({
 get: () => props.modelValue,
 set: (val) => emit('update:modelValue', val)
})

// 把时间戳格式化为可读时间
const formatTimeLabel = (ms) => {
 if (!ms) return ''
 const d = new Date(ms)
 // 简短：HH:mm:ss，如果跨日则带日期
 const today = new Date()
 const sameDay = d.toDateString() === today.toDateString()
 const pad = (n) => String(n).padStart(2, '0')
 const t = `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
 return sameDay ? t : `${d.getMonth() + 1}/${d.getDate()} ${t}`
}

// 格式化数字
const formatNumber = (num) => {
 const n = Number(num) || 0
 return new Intl.NumberFormat('zh-CN').format(Math.round(n))
}

// 格式化字节 —— 修复：bytes <= 0 时 Math.log 会爆炸
const formatBytes = (bytes) => {
 const n = Number(bytes) || 0
 if (n <= 0) return '0 B'
 const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
 const i = Math.min(sizes.length - 1, Math.floor(Math.log(n) / Math.log(1024)))
 return Math.round((n / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i]
}

// 格式化带宽 —— 后端存储的 bandwidth 单位是 MB/s（见 task_service.py total_bw_mbs），
// 必须专门处理，不能直接用 formatBytes（那会把 500MB/s 显示成 500B/s）
const formatMBps = (mbps) => {
 const n = Number(mbps) || 0
 if (n <= 0) return '0 MB/s'
 if (n >= 1024) return (n / 1024).toFixed(2) + ' GB/s'
 if (n >= 1) return n.toFixed(2) + ' MB/s'
 if (n >= 1 / 1024) return (n * 1024).toFixed(2) + ' KB/s'
 return (n * 1024 * 1024).toFixed(0) + ' B/s'
}

// 格式化延迟
const formatLatency = (microseconds) => {
 const us = Number(microseconds) || 0
 if (us < 1000) {
 return Math.round(us) + ' μs'
 } else if (us < 1000000) {
 return Math.round(us / 1000 * 100) / 100 + ' ms'
 } else {
 return Math.round(us / 1000000 * 100) / 100 + ' s'
 }
}

// 格式化百分比
const formatPercent = (value) => {
 return Math.round(value * 100) / 100 + '%'
}

// 刷新性能数据
// 从后端拉取真实性能数据
// 后端接口约定：GET /api/tasks/{task_id}/metrics?limit=120
// 返回：[{ timestamp, iops, bandwidth, latency, cpu_usage }, ...]
// 实际集成时若后端接口不同，只需改这里；整个组件的数据结构保持一致。
const fetchMetricsFromBackend = async () => {
 if (!props.task?.id) return []
 try {
 const { data } = await axios.get(
 `/api/tasks/${props.task.id}/metrics`,
 { params: { limit: MAX_HISTORY } }
 )
 if (Array.isArray(data)) return data
 if (Array.isArray(data?.items)) return data.items
 return []
 } catch (err) {
 console.error('[TaskMetricsDialog] fetch metrics failed:', err)
 return []
 }
}

// 把一条新数据点追加到历史缓存，保持上限
const pushHistory = (point) => {
 metricsHistory.value.push(point)
 if (metricsHistory.value.length > MAX_HISTORY) {
 metricsHistory.value.splice(0, metricsHistory.value.length - MAX_HISTORY)
 }
}

// 刷新性能数据 —— 不再用 Math.random()，改为真实请求
const refreshMetrics = async () => {
 refreshing.value = true
 try {
 const list = await fetchMetricsFromBackend()
 if (list.length > 0) {
 // 用后端返回的完整历史覆盖本地缓存
 metricsHistory.value = list.slice(-MAX_HISTORY)
 // 当前指标 = 最新一条
 const latest = list[list.length - 1] || {}
 currentMetrics.value = {
 iops: Number(latest.iops) || 0,
 bandwidth: Number(latest.bandwidth) || 0,
 latency: Number(latest.latency) || 0,
 cpu_usage: Number(latest.cpu_usage) || 0,
 }
 }
 updateStatistics()
 updateCharts()
 ElMessage.success('性能数据刷新成功')
 } catch (error) {
 console.error('[TaskMetricsDialog] refresh failed:', error)
 ElMessage.error('性能数据刷新失败')
 } finally {
 refreshing.value = false
 }
}

// 实时更新 —— 每次增量拉取最新一条
const tickRealtime = async () => {
 const list = await fetchMetricsFromBackend()
 if (!list.length) return
 const latest = list[list.length - 1]
 const point = {
 timestamp: latest.timestamp || Date.now(),
 iops: Number(latest.iops) || 0,
 bandwidth: Number(latest.bandwidth) || 0,
 latency: Number(latest.latency) || 0,
 cpu_usage: Number(latest.cpu_usage) || 0,
 }
 Object.assign(currentMetrics.value, point)
 pushHistory(point)
 updateStatistics()
 updateCharts()
}

// 更新统计数据 —— 真实聚合，不再等于 current
const updateStatistics = () => {
 const hist = metricsHistory.value
 if (!hist.length) return
 const keys = ['iops', 'bandwidth', 'latency', 'cpu_usage']
 const stats = { peak: {}, min: {}, avg: {}, std: {}, p95: {} }

 for (const key of keys) {
 const values = hist.map(h => Number(h[key]) || 0)
 const sorted = [...values].sort((a, b) => a - b)
 const sum = values.reduce((a, b) => a + b, 0)
 const avg = sum / values.length
 const variance = values.reduce((s, v) => s + (v - avg) ** 2, 0) / values.length
 // p95 用 Excel/nearest-rank，n 小也要稳健
 const idx = Math.min(sorted.length - 1, Math.max(0, Math.ceil(0.95 * sorted.length) - 1))

 stats.peak[key] = Math.max(...values)
 stats.min[key] = Math.min(...values)
 stats.avg[key] = avg
 stats.std[key] = Math.sqrt(variance)
 stats.p95[key] = sorted[idx]
 }
 peakMetrics.value = stats.peak
 minMetrics.value = stats.min
 avgMetrics.value = stats.avg
 stdMetrics.value = stats.std
 p95Metrics.value = stats.p95
}

// 切换实时更新 —— 每次先清理旧定时器，避免重复启动
const toggleRealtime = () => {
 if (realtimeTimer.value) {
 clearInterval(realtimeTimer.value)
 realtimeTimer.value = null
 }
 if (realtimeEnabled.value) {
 realtimeTimer.value = setInterval(tickRealtime, 2000)
 // 立即执行一次，提升首屏响应
 tickRealtime()
 }
}


// ========== 通用图表构造器 ==========
// 为了在时间抖动分析场景下让四张图完全联动，这里抽了一个公共构造器
// 主要改动：
// 1. xAxis.type 从 'category' 改为 'time'，data 使用 [timestamp, value] 二维对，
// 这样 dataZoom 按真实时间切片，时间采样不等距也能正确显示
// 2. 加入 dataZoom: [inside, slider]，用户可以用鼠标滚轮、拖拽、底部滑块自由查看时间窗格
// 3. 同步监听 dataZoom 事件，区分"代码触发"和"用户触发"——用户手动拖动会关闭 followLatest
const makeChartOption = ({ colorLine, colorArea, yAxis, showSlider = true }) => ({
 backgroundColor: 'transparent',
 animation: false, // 实时场景下关掉动画，避免数据频繁更新时视觉晃动
 grid: {
 top: 24,
 right: 24,
 bottom: showSlider ? 60 : 40, // 给 slider 留空间
 left: 70,
 },
 tooltip: {
 trigger: 'axis',
 axisPointer: { type: 'cross', snap: true, lineStyle: { color: '#64748b' } },
 backgroundColor: 'rgba(15,23,42,0.92)',
 borderColor: '#334155',
 textStyle: { color: '#e2e8f0' },
 formatter: (params) => {
 if (!params || !params.length) return ''
 const p = params[0]
 const ts = Array.isArray(p.value) ? p.value[0] : p.axisValue
 return `${formatTimeLabel(ts)}<br/>${p.marker}${p.seriesName}: <b>${yAxis.tooltipFormatter(p.value[1])}</b>`
 },
 },
 xAxis: {
 type: 'time',
 axisLine: { lineStyle: { color: '#475569' } },
 axisLabel: {
 color: '#94a3b8',
 formatter: (value) => {
 const d = new Date(value)
 const pad = (n) => String(n).padStart(2, '0')
 return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
 },
 },
 splitLine: { show: false },
 },
 yAxis: {
 type: 'value',
 max: yAxis.max,
 axisLine: { lineStyle: { color: '#475569' } },
 axisLabel: { color: '#94a3b8', formatter: yAxis.formatter },
 splitLine: { lineStyle: { color: '#334155' } },
 },
 // 关键：dataZoom 实现时间窗格滑动查看
 dataZoom: [
 // 内部式：在图表内拖拽/滚轮缩放
 {
 type: 'inside',
 throttle: 50,
 zoomOnMouseWheel: true,
 moveOnMouseMove: false, // 设成 true 会和 tooltip 冲突，保持默认拖拽即可
 moveOnMouseWheel: false,
 },
 // 滑块式：底部出现可拖动的时间窗格
 ...(showSlider
 ? [{
 type: 'slider',
 height: 22,
 bottom: 8,
 borderColor: '#334155',
 backgroundColor: 'rgba(30,41,59,0.4)',
 fillerColor: 'rgba(59,130,246,0.18)',
 handleStyle: { color: '#3b82f6', borderColor: '#3b82f6' },
 moveHandleStyle: { color: '#3b82f6' },
 textStyle: { color: '#94a3b8' },
 labelFormatter: (value) => formatTimeLabel(value),
 throttle: 50,
 }]
 : []),
 ],
 series: [{
 type: 'line',
 smooth: false, // 抖动分析场景下关闭平滑，否则会把真实的尖刺/毛刺磨平
 showSymbol: false,
 sampling: 'lttb', // 大数据量时下采样保留视觉特征（抖动尖刺不会丢）
 lineStyle: { color: colorLine, width: 1.5 },
 itemStyle: { color: colorLine },
 areaStyle: { color: colorArea },
 data: [],
 }],
})

// 初始化图表
const initCharts = () => {
  // 使用 nextTick 确保 DOM 已渲染
  nextTick(() => {
    if (!iopsChart.value || !bandwidthChart.value || !latencyChart.value) {
      return
    }

   chartInstances.iops = echarts.init(iopsChart.value)
 chartInstances.iops.setOption(
 makeChartOption({
 colorLine: '#3b82f6',
 colorArea: 'rgba(59, 130, 246, 0.1)',
 yAxis: {
 formatter: (v) => Number(v).toLocaleString(),
 tooltipFormatter: (v) => `${formatNumber(v)} IOPS`,
 },
 })
 )
 chartInstances.iops.setOption({ series: [{ name: 'IOPS' }] })

 chartInstances.bandwidth = echarts.init(bandwidthChart.value)
 chartInstances.bandwidth.setOption(
 makeChartOption({
 colorLine: '#10b981',
 colorArea: 'rgba(16, 185, 129, 0.1)',
 yAxis: {
 formatter: (v) => formatMBps(v),
 tooltipFormatter: (v) => formatMBps(v),
 },
 })
 )
 chartInstances.bandwidth.setOption({ series: [{ name: '带宽' }] })

 chartInstances.latency = echarts.init(latencyChart.value)
 chartInstances.latency.setOption(
 makeChartOption({
 colorLine: '#f59e0b',
 colorArea: 'rgba(245, 158, 11, 0.1)',
 yAxis: {
 formatter: (v) => formatLatency(v),
 tooltipFormatter: (v) => formatLatency(v),
 },
 })
 )
 chartInstances.latency.setOption({ series: [{ name: '延迟' }] })

 chartInstances.cpu = echarts.init(cpuChart.value)
 chartInstances.cpu.setOption(
 makeChartOption({
 colorLine: '#6366f1',
 colorArea: 'rgba(99, 102, 241, 0.1)',
 yAxis: {
 max: 100,
 formatter: '{value}%',
 tooltipFormatter: (v) => `${Number(v).toFixed(1)}%`,
 },
 })
 )
 chartInstances.cpu.setOption({ series: [{ name: 'CPU' }] })

 // 关键：让四张图共享 dataZoom —— 拖动任意一张，其他三张同步滑动
 // connect() 是按 group id 关联，所有调用 group=id 的实例会共享 dataZoom 事件
 const group = `perf-jitter-${Math.random().toString(36).slice(2, 8)}`
 Object.values(chartInstances).forEach(ins => {
 if (ins) ins.group = group
 })
 echarts.connect(group)

 // 监听 dataZoom 事件：用户手动操作后关闭"跟随最新"
 // 只在 iops 图上监听即可（联动模式下其他图不会重复派发用户事件）
 chartInstances.iops.on('dataZoom', onZoomByUser)
 chartInstances.bandwidth.on('dataZoom', onZoomByUser)
 chartInstances.latency.on('dataZoom', onZoomByUser)
 chartInstances.cpu.on('dataZoom', onZoomByUser)
  })
}

// 用户操作 dataZoom 时触发：
// - 如果是代码内通过 dispatchAction 主动修改，_zoomProgramming 为 true，跳过
// - 否则认为是用户手动拖动，锁定时间窗格，停止自动跟随
const onZoomByUser = (params) => {
 if (_zoomProgramming) return
 followLatest.value = false
 selectedRange.value = 'custom'
 // 记录当前可见时间范围用于展示
 refreshViewWindowLabel()
}

// 读取图表当前的 dataZoom 状态，反向算出真实时间范围，写进 viewWindow 供 UI 显示
const refreshViewWindowLabel = () => {
 const ins = chartInstances.iops
 if (!ins) return
 const opt = ins.getOption()
 const zoom = opt.dataZoom?.[0]
 if (!zoom) return

 // dataZoom 既可能给 start/end(百分比)，也可能给 startValue/endValue(毫秒)
 if (zoom.startValue != null && zoom.endValue != null) {
 viewWindow.value = { from: zoom.startValue, to: zoom.endValue }
 return
 }
 const hist = metricsHistory.value
 if (!hist.length) return
 const t0 = hist[0].timestamp
 const t1 = hist[hist.length - 1].timestamp
 const span = t1 - t0 || 1
 const startPct = zoom.start ?? 0
 const endPct = zoom.end ?? 100
 viewWindow.value = {
 from: t0 + (span * startPct) / 100,
 to: t0 + (span * endPct) / 100,
 }
}

// ========== 快捷范围切换 ==========
const applyQuickRange = (rangeValue) => {
 selectedRange.value = rangeValue
 const opt = rangeOptions.find(o => o.value === rangeValue)
 if (!opt) return

 const hist = metricsHistory.value
 if (!hist.length) return

 const latest = hist[hist.length - 1].timestamp || Date.now()

 if (opt.value === 'all' || opt.seconds == null) {
 // 全部：回到实时跟随模式，放开 dataZoom 到 0-100%
 followLatest.value = true
 applyZoomToAll({ start: 0, end: 100 })
 viewWindow.value = { from: hist[0].timestamp, to: latest }
 return
 }

 // 固定秒数范围：锁定窗口，不再跟随
 followLatest.value = false
 const from = latest - opt.seconds * 1000
 applyZoomToAll({ startValue: from, endValue: latest })
 viewWindow.value = { from, to: latest }
}

// 回到实时：把 dataZoom 恢复到最新时段（以当前窗口宽度跟随最新数据）
const resumeFollowLatest = () => {
 followLatest.value = true
 selectedRange.value = 'all'
 applyZoomToAll({ start: 0, end: 100 })
}

// 统一把 dataZoom 命令派发到四张图
const applyZoomToAll = (zoomSpec) => {
 _zoomProgramming = true
 try {
 Object.values(chartInstances).forEach(ins => {
 if (!ins || ins.isDisposed?.()) return
 ins.dispatchAction({
 type: 'dataZoom',
 ...zoomSpec,
 })
 })
 } finally {
 // 等当前事件循环清空再复位，确保派发过程中触发的 dataZoom 事件都被忽略
 setTimeout(() => { _zoomProgramming = false }, 0)
 }
}

// ========== 数据更新 ==========
// 更新图表：
// - 把历史数据转成 [timestamp, value] 对喂给 series
// - followLatest=true 时：窗口宽度保持不变，跟到最新时间
// - followLatest=false 时：保持用户当前的 dataZoom 位置不动
const updateCharts = () => {
 if (!metricsHistory.value.length) return
 const hist = metricsHistory.value

 const pack = (key, tr = (v) => v) =>
 hist.map(p => [Number(p.timestamp) || Date.now(), tr(Number(p[key]) || 0)])

 const setSeries = (instance, data) => {
 if (!instance || instance.isDisposed?.()) return
 // notMerge=false 只更新 series.data，避免 setOption 重置 dataZoom 位置
 instance.setOption({ series: [{ data }] })
 }

 setSeries(chartInstances.iops, pack('iops', Math.round))
 setSeries(chartInstances.bandwidth, pack('bandwidth'))
 setSeries(chartInstances.latency, pack('latency'))
 setSeries(chartInstances.cpu, pack('cpu_usage'))

 // followLatest 下主动滚动到最新：
 // 保持当前"时间跨度"不变，窗口右端固定为最新时间戳
 if (followLatest.value) {
 const latest = hist[hist.length - 1].timestamp
 const ins = chartInstances.iops
 if (ins) {
 const opt = ins.getOption()
 const zoom = opt.dataZoom?.[0]
 let windowMs = null
 if (zoom?.startValue != null && zoom?.endValue != null) {
 windowMs = zoom.endValue - zoom.startValue
 }
 // 首次没有明确窗口：默认展示最近 2 分钟；数据不足 2 分钟则展示全部
 if (!windowMs) {
 const spanAll = latest - hist[0].timestamp
 windowMs = Math.min(2 * 60 * 1000, spanAll || 1)
 }
 applyZoomToAll({ startValue: latest - windowMs, endValue: latest })
 viewWindow.value = { from: latest - windowMs, to: latest }
 }
 } else {
 // 用户锁定窗口时，只刷新标签上的真实时间（series 数据变了，百分比对应的时间也变了）
 refreshViewWindowLabel()
 }
}

// 窗口尺寸变化时让所有图表自适应
const handleResize = () => {
 Object.values(chartInstances).forEach(chart => {
 if (chart && !chart.isDisposed?.()) {
 chart.resize()
 }
 })
}

// 初始化
onMounted(() => {
 nextTick(async () => {
 initCharts()
 // 真实拉取，不再用假数据
 await refreshMetrics()
 if (realtimeEnabled.value) {
 toggleRealtime()
 }
 })
 window.addEventListener('resize', handleResize)
})

// 清理
onUnmounted(() => {
 if (realtimeTimer.value) {
 clearInterval(realtimeTimer.value)
 realtimeTimer.value = null
 }
 window.removeEventListener('resize', handleResize)

 // 销毁图表实例
 Object.values(chartInstances).forEach(chart => {
 if (chart && !chart.isDisposed?.()) {
 chart.dispose()
 }
 })
 chartInstances = {}
})

// 关闭对话框时的处理：停止实时更新，避免对话框关了还在轮询
const handleClose = () => {
 if (realtimeEnabled.value) {
 realtimeEnabled.value = false
 toggleRealtime()
 }
 emit('update:modelValue', false)
 emit('close')
}

// 对话框关闭时停止实时轮询
watch(visible, (val) => {
 if (!val && realtimeEnabled.value) {
 realtimeEnabled.value = false
 toggleRealtime()
 }
})
</script>

<style scoped>
/* 不再单独为对话框设深色背景，统一走 style.css 中
   .el-dialog 的浅色兼容层；对话框的色彩和主界面保持一致 */
.metrics-dialog :deep(.el-dialog) {
  border-radius: var(--radius-lg);
}
.metrics-dialog :deep(.el-dialog__header) {
  border-bottom: 1px solid var(--border-2);
}
</style>