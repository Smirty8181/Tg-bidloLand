<template>
  <AppLayout>
    <Navbar subtitle="Живая карта мира" :live="ready" :refreshing="store.refreshing" />

    <Loader v-if="loading" />

    <div v-else class="page-stack page-enter">
      <section class="map-hero mc-panel mc-panel--gold sub-hero">
        <div class="map-hero__head">
          <div class="chip" :class="ready ? 'chip--live' : ''">
            <BlIcon :name="ready ? 'online' : 'offline'" :size="10" />
            {{ ready ? "Карта онлайн" : "Недоступна" }}
          </div>
          <BlIcon name="map" :size="22" tone="gold" />
        </div>

        <h1 class="sub-hero__title mt-3">БыдлоЛенд <span class="text-gold">на карте</span></h1>
        <p class="sub-hero__desc">Исследуй постройки, смотри где игроки и переключай миры — прямо в приложении.</p>

        <div v-if="store.server?.online" class="mini-stat mt-3 !flex-row !items-center !gap-2 !py-2 !px-3 w-fit">
          <BlIcon name="players" :size="14" tone="gold" />
          <span class="mini-stat__value !text-xs">{{ store.server.count ?? 0 }} игроков на сервере</span>
        </div>
      </section>

      <section v-if="ready" class="mc-panel overflow-hidden" style="border-radius: var(--radius-md)">
        <iframe
          :src="url"
          class="map-frame__iframe"
          title="Dynmap"
          loading="lazy"
          referrerpolicy="no-referrer-when-downgrade"
          allow="fullscreen"
        />
        <div class="map-frame__actions">
          <button type="button" class="mc-btn mc-btn--gold pressable flex-1" @click="openExternal">
            <BlIcon name="map" :size="16" tone="gold" />
            В браузере
          </button>
          <button type="button" class="mc-btn pressable" @click="copyLink">
            {{ copied ? "Скопировано" : "Копировать" }}
          </button>
        </div>
      </section>

      <EmptyState
        v-else
        title="Карта скоро появится"
        text="Администратор ещё не указал ссылку на Dynmap. Загляни позже."
        icon="map"
      />

      <section class="mc-panel p-4">
        <p class="label-caps mb-3">Подсказки</p>
        <ul class="map-tips">
          <li v-for="tip in tips" :key="tip">
            <BlIcon name="chevron" :size="12" tone="gold" />
            {{ tip }}
          </li>
        </ul>
      </section>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import AppLayout from "../layouts/AppLayout.vue";
import Navbar from "../components/ui/Navbar.vue";
import BlIcon from "../components/ui/BlIcon.vue";
import Loader from "../components/ui/Loader.vue";
import EmptyState from "../components/ui/EmptyState.vue";
import { api } from "../api/client";
import { useTelegram } from "../composables/useTelegram";
import { usePageRefresh } from "../composables/usePageRefresh";
import { useAppStore } from "../stores/app";

const url = ref("");
const loading = ref(true);
const copied = ref(false);
const store = useAppStore();
const { openLink, haptic } = useTelegram();

const ready = computed(() => Boolean(url.value));

const tips = [
  "Масштабируй колёсиком или жестом pinch",
  "Кликни на игрока — увидишь его позицию",
  "Переключай слои карты в правом верхнем углу",
];

async function loadMap() {
  loading.value = true;
  try {
    const data = await api.map();
    url.value = data.url || "";
  } catch {
    url.value = "";
  } finally {
    loading.value = false;
  }
}

async function reload() {
  haptic("light");
  await Promise.all([store.bootstrap(), loadMap()]);
}

usePageRefresh(reload);

function openExternal() {
  if (!url.value) return;
  haptic("light");
  openLink(url.value);
}

async function copyLink() {
  if (!url.value) return;
  try {
    await navigator.clipboard.writeText(url.value);
    copied.value = true;
    haptic("light");
    window.setTimeout(() => {
      copied.value = false;
    }, 2000);
  } catch {
    copied.value = false;
  }
}

onMounted(async () => {
  store.bootstrap();
  await loadMap();
});
</script>

<style scoped>
.map-hero__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.map-frame__iframe {
  display: block;
  width: 100%;
  height: min(62vh, 520px);
  border: 0;
  background: #111;
}

.map-frame__actions {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid var(--line);
}

.map-tips {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.map-tips li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  line-height: 1.45;
  color: #c8d0e0;
}
</style>
