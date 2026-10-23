<template>
  <nav class="bottom-nav fixed bottom-0 left-0 right-0 z-40 px-4 pb-[calc(10px+var(--safe-bottom))] pt-2">
    <div class="bottom-nav__dock glass-bar mx-auto grid max-w-lg grid-cols-4 gap-0.5 rounded-2xl p-1 shadow-dock">
      <RouterLink
        v-for="item in items"
        :key="item.to"
        :to="item.to"
        class="pressable bottom-nav__item flex flex-col items-center gap-1 rounded-xl py-2.5 transition-colors"
        :class="isActive(item.to) ? 'bottom-nav__item--active' : 'text-muted'"
        @click="haptic()"
      >
        <BlIcon :name="item.icon" :size="20" :tone="isActive(item.to) ? 'gold' : 'muted'" />
        <span class="text-[9px] font-bold uppercase tracking-wide">{{ item.label }}</span>
      </RouterLink>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { useRoute } from "vue-router";
import BlIcon, { type IconName } from "./BlIcon.vue";
import { useTelegram } from "../../composables/useTelegram";

const route = useRoute();
const { haptic } = useTelegram();

const items: { to: string; icon: IconName; label: string }[] = [
  { to: "/", icon: "home", label: "Главная" },
  { to: "/server", icon: "players", label: "Сервер" },
  { to: "/profile", icon: "profile", label: "Профиль" },
  { to: "/more", icon: "more", label: "Ещё" },
];

function isActive(path: string) {
  if (path === "/") return route.path === "/";
  return route.path.startsWith(path);
}
</script>

<style scoped>
.bottom-nav {
  background: linear-gradient(180deg, transparent, rgba(10, 11, 16, 0.95) 30%);
  pointer-events: none;
}

.bottom-nav__dock {
  pointer-events: auto;
}

.bottom-nav__item--active {
  color: var(--gold-soft);
  background: rgba(232, 176, 32, 0.08);
}
</style>
