<template>
  <PullRefresh :refreshing="store.refreshing" @refresh="handleRefresh">
    <div class="app-shell mx-auto min-h-screen max-w-lg px-4 pb-[calc(88px+var(--safe-bottom))] pt-2">
      <div v-if="isDemoMode" class="demo-banner" role="status">
        Демо · вымышленные данные · только просмотр · действия отключены
      </div>
      <div v-if="store.offline" class="offline-banner mb-3">
        <BlIcon name="offline" :size="14" tone="gold" />
        <span>Оффлайн — сохранённые данные{{ cacheLabel }}</span>
      </div>
      <slot />
      <BottomNavigation />
      <Transition name="toast">
        <div v-if="store.toast" class="toast glass-bar fixed bottom-[calc(76px+var(--safe-bottom))] left-1/2 z-50 max-w-[min(92vw,360px)] -translate-x-1/2 rounded-2xl px-4 py-3 text-sm font-semibold text-gold">
          {{ store.toast }}
        </div>
      </Transition>
    </div>
  </PullRefresh>
</template>

<script setup lang="ts">
import { computed } from "vue";
import BottomNavigation from "../components/ui/BottomNavigation.vue";
import PullRefresh from "../components/ui/PullRefresh.vue";
import BlIcon from "../components/ui/BlIcon.vue";
import { providePageRefresh } from "../composables/usePageRefresh";
import { useAppStore } from "../stores/app";
import { isDemoMode } from "../demo/mode";

const store = useAppStore();
const { refresh } = providePageRefresh();

const cacheLabel = computed(() => {
  if (!store.cacheAge) return "";
  const mins = Math.max(1, Math.round((Date.now() - store.cacheAge) / 60000));
  return ` · ${mins} мин назад`;
});

async function handleRefresh() {
  await refresh();
}
</script>

<style scoped>
.demo-banner {
  margin-bottom: 12px;
  padding: 9px 11px;
  border: 1px solid rgba(232, 176, 32, 0.28);
  border-radius: 12px;
  background: rgba(232, 176, 32, 0.08);
  color: var(--gold);
  font-size: 11px;
  font-weight: 700;
  text-align: center;
}

.offline-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(232, 176, 32, 0.2);
  background: rgba(232, 176, 32, 0.06);
  font-size: 12px;
  font-weight: 600;
  color: var(--gold);
}

.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translate(-50%, 8px);
}
</style>
