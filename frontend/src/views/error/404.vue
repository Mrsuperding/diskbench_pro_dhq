<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
    <div class="text-center">
      <div class="mb-8">
        <div class="w-32 h-32 bg-slate-800/50 rounded-full flex items-center justify-center mx-auto mb-6 backdrop-blur-sm border border-slate-700/50">
          <svg class="w-16 h-16 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6-4h6m2 5.291A7.962 7.962 0 0112 15c-2.34 0-4.467-.881-6.08-2.33"></path>
          </svg>
        </div>
        <h1 class="text-6xl font-bold text-white mb-4">404</h1>
        <h2 class="text-2xl font-semibold text-slate-300 mb-2">页面未找到</h2>
        <p class="text-slate-400 max-w-md mx-auto">
          抱歉，您访问的页面不存在或已被移除。请检查URL是否正确，或返回主页继续浏览。
        </p>
      </div>
      
      <div class="space-x-4">
        <button
          @click="$router.back()"
          class="btn-secondary"
        >
          <ArrowLeftIcon class="w-4 h-4 mr-2" />
          返回上一页
        </button>
        <button
          @click="$router.push('/')"
          class="btn-primary"
        >
          <HomeIcon class="w-4 h-4 mr-2" />
          返回首页
        </button>
      </div>
      
      <!-- 装饰元素 -->
      <div class="mt-12 flex justify-center space-x-2">
        <div class="w-2 h-2 bg-slate-600 rounded-full animate-pulse"></div>
        <div class="w-2 h-2 bg-slate-600 rounded-full animate-pulse" style="animation-delay: 0.2s;"></div>
        <div class="w-2 h-2 bg-slate-600 rounded-full animate-pulse" style="animation-delay: 0.4s;"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ArrowLeftIcon, HomeIcon } from '@heroicons/vue/24/outline'
</script>

<style scoped>
.btn-primary {
  @apply bg-primary-600 hover:bg-primary-700 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200 inline-flex items-center;
}

.btn-secondary {
  @apply bg-slate-600 hover:bg-slate-700 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200 inline-flex items-center;
}
</style>