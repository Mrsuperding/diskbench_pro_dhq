<template>
  <div id="app">
    <!-- 路由视图 -->
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>
<script setup>
import { onMounted } from 'vue'
import { useUserStore } from '@stores/user'
import { useWebSocketStore } from '@stores/websocket'

const userStore = useUserStore()
const wsStore = useWebSocketStore()

// 生命周期
onMounted(() => {
  // 初始化WebSocket连接
  if (userStore.isAuthenticated) {
    wsStore.initialize()
  }
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>