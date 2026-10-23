<template>
  <div class="mc-panel px-5 py-8 text-center" style="border-radius: var(--radius-md)">
    <BlIcon name="offline" :size="24" class="mx-auto" />
    <p class="mt-4 font-display text-base font-bold">Не удалось загрузить</p>
    <p class="mt-2 text-sm text-[var(--muted)]">{{ text }}</p>
    <button class="mt-5 inline-flex items-center gap-2 text-sm font-bold text-gold" @click="$emit('retry')">
      <BlIcon name="refresh" :size="14" tone="gold" />
      Повторить
    </button>
  </div>
</template>

<script setup lang="ts">
import BlIcon from "./BlIcon.vue";
defineProps<{ text?: string }>();
defineEmits<{ retry: [] }>();
</script>
