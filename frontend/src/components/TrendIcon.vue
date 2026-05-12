<template>
  <svg
    :class="iconClass"
    class="w-4 h-4"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path
      v-if="trend === 'up'"
      stroke-linecap="round"
      stroke-linejoin="round"
      stroke-width="2"
      d="M7 17l9.2-9.2M17 17V7H7"
    />
    <path
      v-else-if="trend === 'down'"
      stroke-linecap="round"
      stroke-linejoin="round"
      stroke-width="2"
      d="M17 7l-9.2 9.2M7 7v10h10"
    />
    <path
      v-else
      stroke-linecap="round"
      stroke-linejoin="round"
      stroke-width="2"
      d="M8 12h8"
    />
  </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  trend: {
    type: String,
    default: 'stable',
    validator: (value) => ['up', 'down', 'stable'].includes(value)
  }
})

const iconClass = computed(() => {
  switch (props.trend) {
    case 'up':
      return 'text-success-400'
    case 'down':
      return 'text-danger-400'
    default:
      return 'text-slate-400'
  }
})
</script>