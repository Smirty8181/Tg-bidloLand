<template>
  <AppLayout>
    <Navbar :subtitle="player?.nickname || 'Игрок'" :live="Boolean(player?.online)" refreshable :refreshing="loading" @refresh="load" />

    <Loader v-if="loading && !player" />
    <ErrorState v-else-if="error" :text="error" @retry="load" />
    <EmptyState v-else-if="!player" title="Игрок не найден" text="Такого ника нет в базе сервера." icon="players" />

    <div v-else class="space-y-4 page-enter">
      <section class="profile-hero mc-panel mc-panel--gold overflow-hidden rounded-2xl p-5 text-center">
        <div class="profile-hero__ring mx-auto">
          <SkinAvatar size="xl" :nickname="player.nickname" :uuid="player.uuid" />
          <span v-if="player.online" class="profile-hero__status" />
        </div>
        <h1 class="stat-value mt-4 text-2xl font-bold">{{ player.nickname }}</h1>
        <div class="mt-3 flex flex-wrap items-center justify-center gap-2">
          <span class="chip" :class="player.online ? 'chip--live' : ''">
            <BlIcon :name="player.online ? 'online' : 'offline'" :size="10" />
            {{ player.online ? "В игре" : "Не в сети" }}
          </span>
          <span v-if="player.linked" class="chip chip--gold">Привязан к TG</span>
          <span v-if="player.is_whitelisted" class="chip chip--gold">Whitelist</span>
        </div>
      </section>

      <div class="grid grid-cols-3 gap-2.5">
        <div class="stat-pill stat-pill--gold">
          <div class="stat-pill__icon"><BlIcon name="sword" :size="18" tone="gold" /></div>
          <p class="stat-pill__value">{{ player.kills ?? 0 }}</p>
          <p class="stat-pill__label">Убийства</p>
        </div>
        <div class="stat-pill stat-pill--red">
          <div class="stat-pill__icon"><BlIcon name="skull" :size="18" tone="red" /></div>
          <p class="stat-pill__value">{{ player.deaths ?? 0 }}</p>
          <p class="stat-pill__label">Смерти</p>
        </div>
        <div class="stat-pill stat-pill--blue">
          <div class="stat-pill__icon"><BlIcon name="clock" :size="18" tone="blue" /></div>
          <p class="stat-pill__value">{{ hours }}</p>
          <p class="stat-pill__label">Часы</p>
        </div>
      </div>

      <Card>
        <div class="flex items-center justify-between">
          <span class="text-sm text-muted">K/D ratio</span>
          <span class="stat-value text-lg font-bold text-gold">{{ player.kd ?? 0 }}</span>
        </div>
      </Card>

      <a
        v-if="telegramLink"
        :href="telegramLink"
        class="list-row pressable"
        target="_blank"
        rel="noopener"
      >
        <span class="list-row__main">
          <span class="icon-box icon-box--gold h-10 w-10">
            <BlIcon name="link" :size="18" tone="gold" />
          </span>
          Написать в Telegram
        </span>
        <span class="list-row__meta">{{ player.telegram_username ? `@${player.telegram_username}` : "Открыть" }}</span>
      </a>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import AppLayout from "../layouts/AppLayout.vue";
import Navbar from "../components/ui/Navbar.vue";
import BlIcon from "../components/ui/BlIcon.vue";
import SkinAvatar from "../components/ui/SkinAvatar.vue";
import Card from "../components/ui/Card.vue";
import Loader from "../components/ui/Loader.vue";
import ErrorState from "../components/ui/ErrorState.vue";
import EmptyState from "../components/ui/EmptyState.vue";
import { api } from "../api/client";

type PlayerProfile = {
  nickname: string;
  uuid?: string | null;
  online?: boolean;
  linked?: boolean;
  is_whitelisted?: boolean;
  kills?: number;
  deaths?: number;
  playtime_seconds?: number;
  kd?: number;
  telegram_username?: string | null;
};

const route = useRoute();
const loading = ref(true);
const error = ref("");
const player = ref<PlayerProfile | null>(null);

const hours = computed(() => Math.floor((player.value?.playtime_seconds ?? 0) / 3600));

const telegramLink = computed(() => {
  if (!player.value?.linked || !player.value.telegram_username) return null;
  return `https://t.me/${player.value.telegram_username}`;
});

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const nick = String(route.params.name || "");
    player.value = (await api.playerProfile(nick)) as PlayerProfile;
  } catch (err) {
    player.value = null;
    error.value = err instanceof Error ? err.message : "Ошибка загрузки";
  } finally {
    loading.value = false;
  }
}

watch(() => route.params.name, load);
onMounted(load);
</script>
