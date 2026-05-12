<!-- src/components/Breadcrumb.vue -->
<template>
  <div class="breadcrumb">
    <router-link to="/" class="breadcrumb-item">
      <i class="fa fa-home"></i>
      <span>首页</span>
    </router-link>

    <i class="fa fa-angle-right separator-separator"></i>

    <template v-for="(route, index) in matchedRoutes" :key="route.path">
      <router-link
        v-if="index < matchedRoutes.length - 1"
        :to="route.path"
        class="breadcrumb-item"
      >
        <span>{{ route.meta.title }}</span>
      </router-link>

      <span v-else class="breadcrumb-item active">
        {{ route.meta.title }}
      </span>

      <i v-if="index < matchedRoutes.length - 1" class="fa fa-angle-right separator"></i>
    </template>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { computed } from 'vue'

const route = useRoute()

// 计算匹配的路由
const matchedRoutes = computed(() => {
  // 过滤掉登录页和空路由
  return route.matched.filter(
    r => r.path !== '/' && r.path !== '/login' && r.meta.title
  )
})
</script>

<style scoped>
.breadcrumb {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #666;
}

.breadcrumb-item {
  display: flex;
  align-items: center;
  color: #666;
  text-decoration: none;
  transition: color 0.2s;
}

.breadcrumb-item:hover {
  color: #1890ff;
}

.breadcrumb-item.active {
  color: #333;
  font-weight: 500;
}

.breadcrumb-item .fa-home {
  margin-right: 4px;
  font-size: 16px;
}

.separator {
  margin: 0 8px;
  color: #999;
  font-size: 12px;
}
</style>
