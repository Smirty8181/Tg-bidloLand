<template>
  <div class="segment" role="tablist">
    <button
      v-for="tab in tabs"
      :key="tab.id"
      type="button"
      role="tab"
      class="segment__btn pressable"
      :class="{ 'segment__btn--active': modelValue === tab.id }"
      :aria-selected="modelValue === tab.id"
      @click="$emit('update:modelValue', tab.id)"
    >
      <BlIcon v-if="tab.icon" :name="tab.icon" :size="14" :tone="modelValue === tab.id ? 'gold' : 'muted'" />
      {{ tab.label }}
    </button>
  </div>
</template>

<script setup lang="ts">
import BlIcon, { type IconName } from "./BlIcon.vue";

defineProps<{
  modelValue: string;
  tabs: { id: string; label: string; icon?: IconName }[];
}>();

defineEmits<{ "update:modelValue": [value: string] }>();
</script>

<style scoped>
.segment {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(0, 1fr));
  gap: 6px;
  padding: 4px;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.02);
}

.segment__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 38px;
  padding: 0 10px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.02em;
  transition: all 0.2s ease;
}

.segment__btn--active {
  color: var(--gold-soft);
  background: linear-gradient(180deg, rgba(245, 197, 24, 0.18) 0%, rgba(245, 197, 24, 0.06) 100%);
  box-shadow: 0 0 20px rgba(245, 197, 24, 0.12);
}
</style>
