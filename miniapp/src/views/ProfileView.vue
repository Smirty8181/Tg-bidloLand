<template>
  <AppLayout>
    <Navbar subtitle="Игровой профиль" :live="Boolean(store.profile?.online)" refreshable :refreshing="store.refreshing" @refresh="refresh" />

    <Loader v-if="store.loading && !store.profile" />

    <div v-else class="space-y-4 page-enter">
      <section class="profile-hero mc-panel mc-panel--gold overflow-hidden rounded-2xl p-5 text-center">
        <div class="profile-hero__ring mx-auto">
          <SkinAvatar
            size="xl"
            :nickname="store.profile?.minecraft?.nickname"
            :uuid="store.profile?.minecraft?.uuid"
          />
          <span v-if="store.profile?.online" class="profile-hero__status" />
        </div>
        <h1 class="stat-value mt-4 text-2xl font-bold">
          {{ store.profile?.minecraft?.nickname || store.profile?.first_name || "Игрок" }}
        </h1>
        <p v-if="store.profile?.username" class="mt-1 text-sm text-muted">@{{ store.profile.username }}</p>
        <div class="mt-3 flex flex-wrap items-center justify-center gap-2">
          <span class="chip" :class="store.profile?.online ? 'chip--live' : ''">
            <BlIcon :name="store.profile?.online ? 'online' : 'offline'" :size="10" />
            {{ store.profile?.online ? "В игре" : "Не в сети" }}
          </span>
          <span v-if="store.profile?.is_head_admin" class="chip chip--gold">Head Admin</span>
          <span v-else-if="store.profile?.is_admin" class="chip chip--gold">Admin</span>
        </div>
      </section>

      <div class="grid grid-cols-3 gap-2.5">
        <div class="stat-pill stat-pill--gold">
          <div class="stat-pill__icon">
            <BlIcon name="sword" :size="18" tone="gold" />
          </div>
          <p class="stat-pill__value">{{ store.profile?.minecraft?.kills ?? 0 }}</p>
          <p class="stat-pill__label">Убийства</p>
        </div>
        <div class="stat-pill stat-pill--red">
          <div class="stat-pill__icon">
            <BlIcon name="skull" :size="18" tone="red" />
          </div>
          <p class="stat-pill__value">{{ store.profile?.minecraft?.deaths ?? 0 }}</p>
          <p class="stat-pill__label">Смерти</p>
        </div>
        <div class="stat-pill stat-pill--blue">
          <div class="stat-pill__icon">
            <BlIcon name="clock" :size="18" tone="blue" />
          </div>
          <p class="stat-pill__value">{{ hours }}</p>
          <p class="stat-pill__label">Часы</p>
        </div>
      </div>

      <Card>
        <div class="flex items-center justify-between">
          <span class="text-sm text-muted">K/D ratio</span>
          <span class="stat-value text-lg font-bold text-gold">{{ store.profile?.minecraft?.kd ?? 0 }}</span>
        </div>
      </Card>

      <section class="space-y-2">
        <p class="label-caps px-0.5">Аккаунт</p>
        <RouterLink
          v-for="row in rows"
          :key="row.to"
          class="list-row pressable"
          :to="row.to"
        >
          <span class="list-row__main">
            <span class="icon-box icon-box--gold h-10 w-10">
              <BlIcon :name="row.icon" :size="18" tone="gold" />
            </span>
            {{ row.label }}
          </span>
          <span class="list-row__meta">{{ row.value }}</span>
        </RouterLink>
      </section>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import type { IconName } from "../components/ui/BlIcon.vue";
import AppLayout from "../layouts/AppLayout.vue";
import Navbar from "../components/ui/Navbar.vue";
import Card from "../components/ui/Card.vue";
import BlIcon from "../components/ui/BlIcon.vue";
import Loader from "../components/ui/Loader.vue";
import SkinAvatar from "../components/ui/SkinAvatar.vue";
import { useAppStore, clearBootstrapCache } from "../stores/app";
import { useTelegram } from "../composables/useTelegram";

const store = useAppStore();
const { haptic } = useTelegram();
const hours = computed(() => Math.round(((store.profile?.minecraft?.playtime_seconds || 0) / 3600) * 10) / 10);

const rows = computed(() => {
  const p = store.profile;
  const items: { to: string; icon: IconName; label: string; value: string }[] = [
    { to: "/link", icon: "link", label: "Minecraft", value: p?.minecraft?.nickname || "привязать" },
    {
      to: "/whitelist",
      icon: "whitelist",
      label: "Whitelist",
      value: p?.minecraft?.is_whitelisted ? "✓ добавлен" : "нет",
    },
    { to: "/inventory", icon: "chest", label: "Инвентарь", value: "открыть →" },
  ];
  return items;
});

async function refresh() {
  haptic("light");
  clearBootstrapCache();
  await store.bootstrap();
}

onMounted(() => store.bootstrap());
</script>

<style scoped>
.profile-hero__ring {
  position: relative;
  width: 96px;
  height: 96px;
}

.profile-hero__status {
  position: absolute;
  right: 2px;
  bottom: 2px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--green);
  border: 3px solid var(--panel);
  box-shadow: 0 0 12px rgba(62, 207, 142, 0.45);
}
</style>
