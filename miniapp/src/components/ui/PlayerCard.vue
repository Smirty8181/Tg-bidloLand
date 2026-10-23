<template>
  <RouterLink :to="`/player/${encodeURIComponent(name)}`" class="list-row pressable block">
    <div class="list-row__main min-w-0">
      <SkinAvatar size="sm" :nickname="name" class="shrink-0" />
      <div class="min-w-0">
        <p class="truncate font-display text-sm font-bold">{{ name }}</p>
        <div class="mt-1 flex items-center gap-1.5">
          <BlIcon name="online" :size="10" />
          <span class="text-[11px] font-semibold text-[#7dffb0]">В игре</span>
        </div>
      </div>
    </div>
    <BlIcon name="chevron" :size="14" tone="muted" />
  </RouterLink>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";
import BlIcon from "./BlIcon.vue";
import SkinAvatar from "./SkinAvatar.vue";

defineProps<{ name: string; kills?: number; deaths?: number }>();
</script>
