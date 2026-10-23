<template>
  <div
    ref="root"
    class="pull-refresh"
    @touchstart.passive="onTouchStart"
    @touchmove.passive="onTouchMove"
    @touchend="onTouchEnd"
    @touchcancel="onTouchEnd"
  >
    <div class="pull-refresh__indicator" :style="indicatorStyle">
      <span v-if="pulling || refreshing" class="pull-refresh__spinner" :class="{ 'pull-refresh__spinner--spin': refreshing }">
        <BlIcon name="refresh" :size="16" tone="gold" />
      </span>
      <span v-if="!refreshing" class="pull-refresh__label">{{ pullLabel }}</span>
    </div>
    <div class="pull-refresh__content" :style="contentStyle">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import BlIcon from "./BlIcon.vue";

const props = defineProps<{ refreshing?: boolean }>();
const emit = defineEmits<{ refresh: [] }>();

const root = ref<HTMLElement | null>(null);
const startY = ref(0);
const pull = ref(0);
const pulling = ref(false);
const threshold = 72;

const pullLabel = computed(() => (pull.value >= threshold ? "Отпустите" : "Потяните вниз"));
const indicatorStyle = computed(() => ({
  height: `${Math.max(0, pull.value)}px`,
  opacity: pull.value > 8 ? Math.min(1, pull.value / threshold) : 0,
}));
const contentStyle = computed(() => ({
  transform: pull.value > 0 ? `translateY(${pull.value}px)` : undefined,
}));

function atTop() {
  const el = root.value;
  if (!el) return true;
  let node: HTMLElement | null = el;
  while (node && node !== document.body) {
    if (node.scrollTop > 0) return false;
    node = node.parentElement;
  }
  return window.scrollY <= 0;
}

function onTouchStart(e: TouchEvent) {
  if (props.refreshing || !atTop()) return;
  startY.value = e.touches[0]?.clientY ?? 0;
  pulling.value = true;
}

function onTouchMove(e: TouchEvent) {
  if (!pulling.value || props.refreshing) return;
  const y = e.touches[0]?.clientY ?? 0;
  const delta = y - startY.value;
  if (delta <= 0) {
    pull.value = 0;
    return;
  }
  pull.value = Math.min(delta * 0.45, threshold + 24);
}

function onTouchEnd() {
  if (!pulling.value) return;
  pulling.value = false;
  if (pull.value >= threshold && !props.refreshing) emit("refresh");
  pull.value = 0;
}
</script>

<style scoped>
.pull-refresh {
  position: relative;
}

.pull-refresh__indicator {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 8px;
  overflow: hidden;
  transition: height 0.2s ease, opacity 0.2s ease;
}

.pull-refresh__label {
  font-size: 11px;
  font-weight: 700;
  color: var(--muted);
  padding-bottom: 8px;
}

.pull-refresh__spinner {
  display: inline-flex;
  padding-bottom: 8px;
}

.pull-refresh__spinner--spin {
  animation: spin 0.8s linear infinite;
}

.pull-refresh__content {
  transition: transform 0.2s ease;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
