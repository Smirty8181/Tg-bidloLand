<template>
  <AppLayout>
    <Navbar
      :subtitle="serverLine"
      :live="Boolean(server?.online)"
      :refreshing="store.refreshing"
    />

    <Loader v-if="store.loading && !store.profile" />
    <ErrorState v-else-if="store.error && !store.profile" :text="store.error" @retry="refresh" />

    <div v-else class="space-y-3.5 page-enter stagger">
      <section class="brand-hero">
        <img src="/avatar-hero.jpg" alt="" class="brand-hero__bg" />
        <div class="brand-hero__overlay">
          <h1 class="brand-title">БЫДЛОЛЕНД</h1>
          <p class="brand-hero__tagline">Minecraft × Telegram</p>
        </div>
      </section>

      <div class="mini-stats">
        <div class="mini-stat">
          <div class="mini-stat__icon">
            <BlIcon name="server" :size="18" tone="muted" />
          </div>
          <span class="mini-stat__value">{{ versionLabel }}</span>
          <span class="mini-stat__label">Версия</span>
        </div>
        <div class="mini-stat" :class="server?.online ? 'mini-stat--live' : ''">
          <div class="mini-stat__icon">
            <BlIcon name="players" :size="18" :tone="server?.online ? 'gold' : 'muted'" />
          </div>
          <span class="mini-stat__value">{{ server?.count ?? 0 }} / {{ server?.max ?? 20 }}</span>
          <span class="mini-stat__label">Онлайн</span>
        </div>
        <RouterLink v-if="mapReady" to="/map" class="mini-stat pressable">
          <div class="mini-stat__icon">
            <BlIcon name="map" :size="18" tone="gold" />
          </div>
          <span class="mini-stat__value">Открыть</span>
          <span class="mini-stat__label">Карта мира</span>
        </RouterLink>
        <div v-else class="mini-stat opacity-50">
          <div class="mini-stat__icon">
            <BlIcon name="map" :size="18" tone="muted" />
          </div>
          <span class="mini-stat__value">—</span>
          <span class="mini-stat__label">Карта</span>
        </div>
      </div>

      <JoinServerBlock :status="server" />

      <section v-if="newsPreview.length">
        <div class="section-head">
          <BlIcon name="news" :size="14" tone="gold" />
          <p class="label-caps !mb-0">Новости</p>
          <RouterLink v-if="newsPreview.length > 1" to="/news" class="ml-auto text-xs text-gold">Все</RouterLink>
        </div>
        <article v-for="item in newsPreview" :key="item.id" class="news-card">
          <p class="news-card__title">{{ item.title }}</p>
          <p class="news-card__body">{{ item.text }}</p>
          <p class="news-card__date">{{ formatDate(item.created_at) }}</p>
        </article>
      </section>

      <LinkOnboarding :linked="Boolean(store.profile?.minecraft?.nickname)" />

      <section v-if="store.profile?.minecraft?.nickname" class="status-banner status-banner--ok">
        <BlIcon name="online" :size="16" tone="gold" />
        <div>
          <p class="font-bold">{{ store.profile.minecraft.nickname }} привязан</p>
          <p class="mt-1 text-xs opacity-90">Инвентарь, whitelist и профиль доступны</p>
        </div>
      </section>

      <section>
        <div class="section-head">
          <BlIcon name="bolt" :size="14" tone="gold" />
          <p class="label-caps !mb-0">Быстрые действия</p>
        </div>
        <div class="action-grid">
          <RouterLink
            v-for="item in actions"
            :key="item.to"
            :to="item.to"
            class="action-tile pressable"
            :class="`action-tile--${item.tone}`"
          >
            <div class="action-tile__head">
              <div class="action-tile__icon">
                <BlIcon :name="item.icon" :size="20" tone="gold" />
              </div>
              <BlIcon name="chevron" :size="14" tone="muted" />
            </div>
            <div>
              <p class="action-tile__title">{{ item.label }}</p>
              <p class="action-tile__hint">{{ item.hint }}</p>
            </div>
          </RouterLink>
        </div>
      </section>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import type { IconName } from "../components/ui/BlIcon.vue";
import AppLayout from "../layouts/AppLayout.vue";
import Navbar from "../components/ui/Navbar.vue";
import BlIcon from "../components/ui/BlIcon.vue";
import JoinServerBlock from "../components/ui/JoinServerBlock.vue";
import { formatDate } from "../services/format";
import type { NewsItem } from "../types";
import Loader from "../components/ui/Loader.vue";
import ErrorState from "../components/ui/ErrorState.vue";
import LinkOnboarding from "../components/ui/LinkOnboarding.vue";
import { useAppStore, clearBootstrapCache } from "../stores/app";
import { api } from "../api/client";
import { usePageRefresh } from "../composables/usePageRefresh";

const store = useAppStore();
const mapReady = ref(false);
const newsPreview = ref<NewsItem[]>([]);

const server = computed(() => store.server);
const serverLine = computed(() => (server.value?.online ? "Сервер онлайн" : "Сервер оффлайн"));
const versionLabel = computed(() => {
  const v = server.value?.version || "1.21.10";
  return v.replace("Paper ", "");
});

const actions: { to: string; icon: IconName; label: string; hint: string; tone: "purple" | "green" | "blue" | "red" }[] = [
  { to: "/server", icon: "players", label: "Игроки", hint: "Кто на сервере", tone: "purple" },
  { to: "/inventory", icon: "chest", label: "Инвентарь", hint: "Ваши предметы", tone: "green" },
  { to: "/map", icon: "map", label: "Карта", hint: "Исследуй мир", tone: "blue" },
  { to: "/more", icon: "report", label: "Правила", hint: "Все правила", tone: "red" },
];

async function refresh() {
  clearBootstrapCache();
  await store.bootstrap();
  try {
    const [mapData, newsData] = await Promise.all([api.map(), api.news()]);
    mapReady.value = Boolean((mapData as { url?: string }).url);
    const items = ((newsData as { items?: NewsItem[] }).items || []).slice(0, 2);
    newsPreview.value = items;
  } catch {
    mapReady.value = false;
    newsPreview.value = [];
  }
}

usePageRefresh(refresh);

onMounted(refresh);
</script>
