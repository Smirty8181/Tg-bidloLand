<template>
  <AppLayout>
    <Navbar subtitle="Игроки онлайн" :live="displayCount > 0" refreshable :refreshing="loading" @refresh="load" />

    <div class="search-panel mc-input-wrap">
      <span class="mc-input-wrap__icon"><BlIcon name="players" :size="16" tone="muted" /></span>
      <input v-model="query" class="mc-input" placeholder="Поиск игрока..." />
    </div>

    <Loader v-if="loading && !players.length" />
    <ErrorState v-else-if="error" :text="error" @retry="load" />
    <EmptyState
      v-else-if="!filtered.length && !hiddenOnline"
      :title="query ? 'Игрок не найден' : 'Сервер пуст'"
      :text="query ? 'Попробуй другой ник.' : 'Сейчас на сервере никого нет.'"
      icon="players"
    />

    <div v-else class="page-stack page-enter stagger">
      <div class="mini-stats">
        <div class="mini-stat mini-stat--live">
          <div class="mini-stat__icon">
            <BlIcon name="online" :size="18" tone="gold" />
          </div>
          <span class="mini-stat__value">{{ displayCount }}</span>
          <span class="mini-stat__label">Онлайн</span>
        </div>
        <div class="mini-stat">
          <div class="mini-stat__icon">
            <BlIcon name="players" :size="18" tone="muted" />
          </div>
          <span class="mini-stat__value">{{ filtered.length }}</span>
          <span class="mini-stat__label">В списке</span>
        </div>
        <div class="mini-stat">
          <div class="mini-stat__icon">
            <BlIcon name="server" :size="18" tone="muted" />
          </div>
          <span class="mini-stat__value">{{ serverMax }}</span>
          <span class="mini-stat__label">Макс.</span>
        </div>
      </div>

      <section v-if="hiddenOnline" class="mc-panel mc-panel--gold sub-hero">
        <div class="flex items-center gap-2">
          <BlIcon name="players" :size="18" tone="gold" />
          <p class="sub-hero__title text-sm">Список скрыт сервером</p>
        </div>
        <p class="sub-hero__desc">
          На сервере сейчас {{ playerCount }} {{ playersLabel }}, но Paper не отдаёт ники в публичный список.
        </p>
      </section>

      <PlayerCard v-for="name in filtered" :key="name" :name="name" />
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import AppLayout from "../layouts/AppLayout.vue";
import Navbar from "../components/ui/Navbar.vue";
import BlIcon from "../components/ui/BlIcon.vue";
import PlayerCard from "../components/ui/PlayerCard.vue";
import Loader from "../components/ui/Loader.vue";
import ErrorState from "../components/ui/ErrorState.vue";
import EmptyState from "../components/ui/EmptyState.vue";
import { api } from "../api/client";
import { useAppStore } from "../stores/app";

type PlayersResponse = {
  online?: boolean;
  count?: number;
  max?: number;
  players?: string[];
  players_hidden?: boolean;
};

const store = useAppStore();
const loading = ref(true);
const error = ref("");
const players = ref<string[]>([]);
const playerCount = ref(0);
const serverMax = ref(20);
const playersHidden = ref(false);
const query = ref("");

const filtered = computed(() => players.value.filter((name) => name.toLowerCase().includes(query.value.toLowerCase())));
const hiddenOnline = computed(() => playersHidden.value && playerCount.value > 0 && !filtered.value.length);
const displayCount = computed(() => (playerCount.value > 0 ? playerCount.value : players.value.length));

const playersLabel = computed(() => {
  const n = displayCount.value;
  if (n % 10 === 1 && n % 100 !== 11) return "игрок";
  if ([2, 3, 4].includes(n % 10) && ![12, 13, 14].includes(n % 100)) return "игрока";
  return "игроков";
});

async function load() {
  loading.value = true;
  error.value = "";
  try {
    await store.bootstrap();
    const data = (await api.players()) as PlayersResponse;
    players.value = data.players || [];
    playerCount.value = data.count ?? players.value.length;
    serverMax.value = data.max ?? store.server?.max ?? 20;
    playersHidden.value = Boolean(data.players_hidden);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Ошибка";
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>
