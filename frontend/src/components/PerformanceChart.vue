<template>
  <div class="bg-white rounded-lg shadow p-4">
    <div class="flex justify-between items-center mb-4">
      <h3 class="text-lg font-medium text-gray-900">{{ title }}</h3>
      <div class="flex space-x-2">
        <el-button
          v-for="option in timeOptions"
          :key="option.value"
          :type="selectedTimeRange === option.value ? 'primary' : ''"
          size="small"
          @click="selectedTimeRange = option.value"
        >
          {{ option.label }}
        </el-button>
      </div>
    </div>
    <div ref="chartRef" class="w-full" :style="{ height: height + 'px' }"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import * as echarts from 'echarts'
import { useDebounceFn } from '@vueuse/core'

const props = defineProps({
  title: {
    type: String,
    default: '性能图表'
  },
  data: {
    type: Array,
    default: () => []
  },
  type: {
    type: String,
    default: 'line' // line, bar, gauge
  },
  height: {
    type: Number,
    default: 300
  },
  realTime: {
    type: Boolean,
    default: false
  }
})

const chartRef = ref(null)
let chartInstance = null

const selectedTimeRange = ref('1h')

const timeOptions = [
  { label: '1分钟', value: '1m' },
  { label: '5分钟', value: '5m' },
  { label: '1小时', value: '1h' },
  { label: '6小时', value: '6h' },
  { label: '24小时', value: '24h' }
]

// 修复：
// - xAxis.type = 'time' 要求数值时间戳（ms）或 Date 对象
//   但上游很多地方传的是 new Date().toLocaleTimeString('zh-CN')，是本地化字符串，
//   会被 ECharts 当作 NaN 处理，时间轴整个错乱。
//   这里把 timestamp 统一规范化。
// - gauge 模式下漏了 grid/xAxis/yAxis 清空会与 line 模式配置冲突。
const normalizeTs = (ts) => {
  if (ts == null) return Date.now()
  if (typeof ts === 'number') return ts
  if (ts instanceof Date) return ts.getTime()
  // ISO 字符串、任何可被 Date 解析的字符串
  const parsed = Date.parse(String(ts))
  if (!Number.isNaN(parsed)) return parsed
  // 实在无法解析就用当前时间兜底，避免整条系列崩掉
  return Date.now()
}

const safeNum = (v) => {
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}

const chartOption = computed(() => {
  if (props.type === 'gauge') {
    return {
      series: [
        {
          type: 'gauge',
          detail: {
            formatter: '{value}%',
            fontSize: 20
          },
          data: [{ value: safeNum(props.data[0]?.value), name: props.title }]
        }
      ]
    }
  }

  const rows = Array.isArray(props.data) ? props.data : []

  const baseOption = {
    grid: {
      top: 40,
      right: 20,
      bottom: 40,
      left: 60
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['读IOPS', '写IOPS', '读吞吐量', '写吞吐量']
    },
    xAxis: {
      type: 'time',
      boundaryGap: false
    },
    yAxis: [
      {
        type: 'value',
        name: 'IOPS',
        position: 'left',
        axisLabel: {
          formatter: '{value}'
        }
      },
      {
        type: 'value',
        name: '吞吐量(MB/s)',
        position: 'right',
        axisLabel: {
          formatter: '{value}'
        }
      }
    ],
    series: [
      {
        name: '读IOPS',
        type: 'line',
        yAxisIndex: 0,
        data: rows.map(item => [normalizeTs(item.timestamp), safeNum(item.readIops)]),
        smooth: true,
        itemStyle: { color: '#3b82f6' }
      },
      {
        name: '写IOPS',
        type: 'line',
        yAxisIndex: 0,
        data: rows.map(item => [normalizeTs(item.timestamp), safeNum(item.writeIops)]),
        smooth: true,
        itemStyle: { color: '#ef4444' }
      },
      {
        name: '读吞吐量',
        type: 'line',
        yAxisIndex: 1,
        data: rows.map(item => [normalizeTs(item.timestamp), safeNum(item.readThroughput)]),
        smooth: true,
        itemStyle: { color: '#10b981' }
      },
      {
        name: '写吞吐量',
        type: 'line',
        yAxisIndex: 1,
        data: rows.map(item => [normalizeTs(item.timestamp), safeNum(item.writeThroughput)]),
        smooth: true,
        itemStyle: { color: '#f59e0b' }
      }
    ]
  }

  return baseOption
})

const initChart = () => {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value)
    chartInstance.setOption(chartOption.value)
  }
}

const updateChart = () => {
  if (chartInstance) {
    chartInstance.setOption(chartOption.value)
  }
}

const resizeChart = useDebounceFn(() => {
  if (chartInstance) {
    chartInstance.resize()
  }
}, 300)

onMounted(() => {
  initChart()
  window.addEventListener('resize', resizeChart)
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
  }
  window.removeEventListener('resize', resizeChart)
})

watch(() => props.data, updateChart, { deep: true })
watch(selectedTimeRange, (newRange) => {
  // 这里可以根据时间范围过滤数据
  updateChart()
})
</script>