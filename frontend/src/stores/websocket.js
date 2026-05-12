import { defineStore } from 'pinia'
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { io } from 'socket.io-client'
import { useUserStore } from './user'

export const useWebSocketStore = defineStore('websocket', () => {
  // 状态
  const socket = ref(null)
  const isConnected = ref(false)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 10
  const messageQueue = ref([])
  const receivedMessages = ref([])
  const connectionUrl = ref('http://localhost:8000') // Socket.IO连接地址（与后端FastAPI端口一致）

  // 计算属性
  const connectionStatus = computed(() => {
    return isConnected.value ? '已连接' : '未连接'
  })

  // 方法
  const initialize = () => {
    // 确保用户已认证
    const userStore = useUserStore()
    if (userStore.isAuthenticated) {
      connect()
    }
  }
  
  const connect = () => {
    // 如果已经连接，则先断开
    if (socket.value) {
      disconnect()
    }

    try {
      const userStore = useUserStore()

      // 创建新的Socket.IO连接（静默模式，减少日志输出）
      socket.value = io(connectionUrl.value, {
        reconnection: true,
        reconnectionAttempts: maxReconnectAttempts,
        reconnectionDelay: 1000,
        timeout: 10000,
        auth: {
          user_id: userStore.userId,
          username: userStore.username
        },
        transports: ['polling', 'websocket'],
        logger: false  // 关闭 socket.io 内部日志
      })

      // 连接错误处理（使用 warn 级别，避免错误日志）
      socket.value.on('connect_error', (error) => {
        // 连接错误是预期行为（服务器可能未运行），使用 warn 而不是 error
        console.warn('Socket.IO 连接失败 (WebSocket 服务可能未启动):', error.message)
      })

      socket.value.on('connect_timeout', () => {
        console.warn('Socket.IO 连接超时')
      })

      // 连接成功处理
      socket.value.on('connect', () => {
        console.log('Socket.IO连接成功')
        isConnected.value = true
        reconnectAttempts.value = 0

        // 发送队列中的消息
        sendQueuedMessages()
      })

      // 接收连接确认
      socket.value.on('connected', (data) => {
        console.log('收到连接确认:', data)
      })

      // 接收任务更新
      socket.value.on('task_update', (data) => {
        console.log('收到任务更新:', data)
        receivedMessages.value.push({ type: 'task_update', data })
        handleMessage({ type: 'task_update', data })
      })

      // 接收性能数据
      socket.value.on('performance_update', (data) => {
        console.log('收到性能数据:', data)
        receivedMessages.value.push({ type: 'performance_update', data })
        handleMessage({ type: 'performance_update', data })
      })

      // 接收系统状态更新
      socket.value.on('system_status_update', (data) => {
        console.log('收到系统状态更新:', data)
        receivedMessages.value.push({ type: 'system_status_update', data })
        handleMessage({ type: 'system_status_update', data })
      })

      // 连接关闭处理
      socket.value.on('disconnect', (reason) => {
        if (reason !== 'io client disconnect') {
          console.warn('Socket.IO连接关闭:', reason)
        }
        isConnected.value = false
      })
    } catch (error) {
      console.warn('创建Socket.IO连接失败:', error.message)
      isConnected.value = false
    }
  }

  const disconnect = () => {
    if (socket.value) {
      socket.value.disconnect()
      socket.value = null
      isConnected.value = false
      console.log('Socket.IO连接已手动关闭')
    }
  }

  const reconnect = () => {
    reconnectAttempts.value++
    // 静默重连，不输出日志
    connect()
  }

  const sendMessage = (event, data = {}) => {
    if (isConnected.value && socket.value) {
      try {
        socket.value.emit(event, data)
        return true
      } catch (error) {
        // 静默失败，不输出错误日志
        messageQueue.value.push({ event, data })
        return false
      }
    } else {
      // 未连接时静默加入队列
      messageQueue.value.push({ event, data })
      return false
    }
  }

  const sendQueuedMessages = () => {
    if (isConnected.value && messageQueue.value.length > 0) {
      // 复制队列并清空
      const messagesToSend = [...messageQueue.value]
      messageQueue.value = []

      // 发送所有消息
      messagesToSend.forEach(({ event, data }) => {
        sendMessage(event, data)
      })
    }
  }

  const handleMessage = (message) => {
    // 根据消息类型进行处理（静默处理，不输出日志）
    switch (message.type) {
      case 'task_update':
        // 任务更新处理
        break
      case 'performance_update':
        // 性能数据处理
        break
      case 'system_status_update':
        // 系统状态更新处理
        break
      default:
        // 未知消息类型，静默忽略
        break
    }
  }

  const clearReceivedMessages = () => {
    receivedMessages.value = []
  }

  const setConnectionUrl = (url) => {
    connectionUrl.value = url
    // 如果已经连接，则重新连接
    if (isConnected.value) {
      reconnect()
    }
  }

  // 自动连接（静默模式）
  onMounted(() => {
    connect()
  })

  // 自动断开
  onUnmounted(() => {
    disconnect()
  })

  return {
    socket,
    isConnected,
    connectionStatus,
    reconnectAttempts,
    receivedMessages,
    connectionUrl,

    initialize,
    connect,
    disconnect,
    reconnect,
    sendMessage,
    clearReceivedMessages,
    setConnectionUrl
  }
})
