<template>
  <n-card>
    <template #header>
      <n-space justify="space-between">
        <span>{{ metricName }} 历史趋势</span>
        <n-button @click="$router.back()">返回</n-button>
      </n-space>
    </template>
    <v-chart :option="opt" autoresize style="height:450px" />
  </n-card>
</template>

<script setup>
// 修复：
// 1. 原代码用了 ref 但没 import，页面一打开就崩溃
// 2. Y 轴单位硬编码为 '%'，IOPS/带宽/延迟都会显示错误单位
// 3. legend 未注册，有多条线时不显示
// 4. 错误处理缺失
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'

use([
  CanvasRenderer,
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
])

const route = useRoute()
const metricName = route.query.name || 'Metric'
const metricKey = route.query.key || 'cpu'
const data = ref([])          // 修复：原来直接 const data = ref([]) 但没 import ref
const loading = ref(false)
const errorMsg = ref('')

// 根据指标类型决定单位和格式化方式
const unitInfo = computed(() => {
  const key = String(metricKey).toLowerCase()
  if (key.includes('cpu') || key.includes('mem') || key.includes('util')) {
    return { name: '%', formatter: v => `${Number(v).toFixed(1)}%` }
  }
  if (key.includes('iops')) {
    return { name: 'IOPS', formatter: v => Number(v).toLocaleString() }
  }
  if (key.includes('bw') || key.includes('bandwidth') || key.includes('throughput')) {
    return { name: 'MB/s', formatter: v => `${Number(v).toFixed(2)} MB/s` }
  }
  if (key.includes('lat') || key.includes('latency')) {
    return { name: 'ms', formatter: v => `${Number(v).toFixed(2)} ms` }
  }
  return { name: '', formatter: v => String(v) }
})

onMounted(async () => {
  loading.value = true
  try {
    const { data: raw } = await axios.get('/api/monitor/history', {
      params: { hours: 24 },
    })
    data.value = Array.isArray(raw) ? raw : []
  } catch (err) {
    console.error('[chart] fetch history failed:', err)
    errorMsg.value = err?.message || 'failed to fetch history'
    data.value = []
  } finally {
    loading.value = false
  }
})

const opt = computed(() => ({
  tooltip: {
    trigger: 'axis',
    valueFormatter: unitInfo.value.formatter,
  },
  legend: { data: [metricName] },
  grid: { left: 60, right: 30, top: 40, bottom: 40 },
  xAxis: {
    type: 'category',
    data: data.value.map(d => d.ts),
    boundaryGap: false,
  },
  yAxis: {
    type: 'value',
    name: unitInfo.value.name,
    axisLabel: { formatter: unitInfo.value.formatter },
  },
  series: [
    {
      name: metricName,
      type: 'line',
      smooth: true,
      areaStyle: {},
      data: data.value.map(d => d[metricKey]),
    },
  ],
}))
</script>
