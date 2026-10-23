<template>
  <div class="space-y-3">
    <div v-for="n in count" :key="n" class="mc-panel h-20 animate-pulse" style="border-radius: var(--radius-md)" />
  </div>
</template>
<script setup lang="ts">
withDefaults(defineProps<{ count?: number }>(), { count: 3 });
</script>
