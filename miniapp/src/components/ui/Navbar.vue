<template>
  <header class="navbar glass-bar sticky top-0 z-30 -mx-1 mb-3 flex items-center gap-3 rounded-2xl px-3 py-2.5">
    <div class="avatar-frame navbar__logo-wrap shrink-0">
      <img src="/logo.jpg" class="navbar__logo avatar-frame__inner" alt="" />
    </div>
    <div class="min-w-0 flex-1">
      <p class="navbar__title">БЫДЛОЛЕНД</p>
      <p class="navbar__status">
        <span class="navbar__dot" :class="live ? 'navbar__dot--on' : ''" />
        {{ subtitle }}
      </p>
    </div>
    <div class="flex shrink-0 items-center gap-2">
      <button
        v-if="refreshable"
        type="button"
        class="navbar__icon-btn pressable"
        aria-label="Обновить"
        :disabled="refreshing"
        @click="onRefresh"
      >
        <span :class="refreshing ? 'navbar__spin' : ''">
          <BlIcon name="refresh" :size="15" tone="muted" />
        </span>
      </button>
      <div v-if="live" class="chip chip--live">
        <BlIcon name="online" :size="9" />
        LIVE
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { inject } from "vue";
import BlIcon from "./BlIcon.vue";
import { APP_REFRESH_KEY } from "../../composables/usePageRefresh";

withDefaults(
  defineProps<{
    subtitle?: string;
    live?: boolean;
    refreshable?: boolean;
    refreshing?: boolean;
  }>(),
  { subtitle: "Сервер онлайн", live: false, refreshable: true, refreshing: false },
);

const appRefresh = inject(APP_REFRESH_KEY, null);

async function onRefresh() {
  if (appRefresh) await appRefresh();
}
</script>

<style scoped>
.navbar__logo-wrap {
  width: 44px;
  height: 44px;
}

.navbar__logo {
  width: 40px;
  height: 40px;
}

.navbar__title {
  margin: 0;
  font-family: Unbounded, Manrope, sans-serif;
  font-size: 15px;
  font-weight: 800;
  line-height: 1;
  color: var(--gold-soft);
}

.navbar__status {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 4px 0 0;
  font-size: 11px;
  font-weight: 600;
  color: var(--muted);
}

.navbar__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--muted);
  flex-shrink: 0;
}

.navbar__dot--on {
  background: var(--green);
  box-shadow: 0 0 8px rgba(62, 207, 142, 0.5);
}

.navbar__icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 11px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.03);
}

.navbar__spin {
  display: inline-flex;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
