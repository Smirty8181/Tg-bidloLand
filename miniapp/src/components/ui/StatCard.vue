<template>
  <div class="stat-pill stat-pill--gold !gap-4 !py-3 !px-3">
    <p class="stat-pill__label !text-[9px]">{{ label }}</p>
    <p class="stat-pill__value !text-xl">{{ value }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{ label: string; value: string | number }>();
</script>
