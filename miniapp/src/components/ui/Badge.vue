<template>
  <span class="inline-flex items-center gap-1.5 rounded-sm px-2 py-1 text-[10px] font-bold uppercase tracking-wider" :class="toneClass">
    <BlIcon v-if="dotIcon" :name="dotIcon" :size="10" />
    <slot />
  </span>
</template>

<script setup lang="ts">
import { computed } from "vue";
import BlIcon, { type IconName } from "./BlIcon.vue";

const props = defineProps<{ tone?: "ok" | "warn" | "bad" | "info" }>();

const toneClass = computed(() => {
  if (props.tone === "ok") return "bg-[#1a2e22] text-[#7dffb0] border border-[#2d5a3d]";
  if (props.tone === "warn") return "bg-[#2e2618] text-[#f5c518] border border-[#5a4a1a]";
  if (props.tone === "bad") return "bg-[#2e1818] text-[#ff8a8a] border border-[#5a2a2a]";
  return "bg-[#18202e] text-[#8ab4ff] border border-[#2a3f5a]";
});

const dotIcon = computed<IconName | undefined>(() => {
  if (props.tone === "ok") return "online";
  if (props.tone === "bad") return "offline";
  return undefined;
});
</script>
