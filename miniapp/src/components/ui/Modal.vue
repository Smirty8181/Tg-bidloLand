<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-4 sm:items-center" @click.self="$emit('close')">
      <div class="mc-panel w-full max-w-md p-5 page-enter" style="border-radius: var(--radius-lg)">
        <h3 class="font-display text-lg font-bold">{{ title }}</h3>
        <p v-if="text" class="mt-2 text-sm text-[var(--muted)] whitespace-pre-line">{{ text }}</p>
        <div class="mt-4 space-y-2">
          <slot />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{ open: boolean; title: string; text?: string }>();
defineEmits<{ close: [] }>();
</script>
