<template>
  <section class="mc-panel page-enter p-4" :class="{ 'mc-panel--gold': accent }">
    <slot />
  </section>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ accent?: boolean }>(), { accent: false });
</script>
