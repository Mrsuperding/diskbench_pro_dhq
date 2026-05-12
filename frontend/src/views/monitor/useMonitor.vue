import { ref } from 'vue'

const cpu = ref(0)
const mem = ref(0)
const disk = ref(0)
const history = ref([])

let ws = null

export function useMonitor() {
  function connect(onMessage) {
    ws = new WebSocket('ws://localhost:8000/ws')
    ws.onmessage = e => {
      const sample = JSON.parse(e.data)
      cpu.value = sample.cpu
      mem.value = sample.mem
      disk.value = sample.disk
      history.value.push(sample)
      if (history.value.length > 300) history.value.shift()
      onMessage && onMessage(sample)
    }
    ws.onerror = () => window.$message.error('WebSocket 连接失败')
    return ws
  }

  function disconnect() {
    ws && ws.close()
    ws = null
  }

  return { cpu, mem, disk, history, connect, disconnect }
}