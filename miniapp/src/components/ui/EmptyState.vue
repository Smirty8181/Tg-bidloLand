<template>
  <div class="mc-panel rounded-2xl px-5 py-12 text-center">
    <div v-if="icon" class="icon-box mx-auto h-16 w-16">
      <BlIcon :name="icon" :size="30" tone="muted" />
    </div>
    <img v-else src="/logo.jpg" alt="" class="mx-auto h-16 w-16 rounded-2xl border border-[var(--line)] object-cover opacity-70" />
    <p class="mt-5 font-display text-base font-bold">{{ title }}</p>
    <p class="mx-auto mt-2 max-w-[28ch] text-sm leading-relaxed text-muted">{{ text }}</p>
    <slot />
  </div>
</template>

<script setup lang="ts">
import BlIcon, { type IconName } from "./BlIcon.vue";

withDefaults(defineProps<{ title?: string; text?: string; icon?: IconName }>(), {
  title: "Здесь пока ничего нет",
  text: "Как только появятся данные, они отобразятся здесь.",
});
</script>
