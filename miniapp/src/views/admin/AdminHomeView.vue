<template>

  <AppLayout>

    <Navbar subtitle="Админ-панель" refreshable :refreshing="loading" @refresh="load" />

    <Loader v-if="loading && !stats.users" />

    <ErrorState v-else-if="error" :text="error" @retry="load" />

    <div v-else class="page-stack page-enter stagger">

      <ServerHero v-if="serverStatus" :status="serverStatus" :is-admin="true" />

      <section v-if="serverMetrics.length" class="mc-panel">
        <div class="section-head !mb-3">
          <BlIcon name="server" :size="14" tone="gold" />
          <p class="label-caps !mb-0">Метрики сервера</p>
        </div>
        <div class="grid grid-cols-3 gap-2">
          <div v-for="metric in serverMetrics" :key="metric.label" class="mini-stat">
            <span class="mini-stat__value !text-sm">{{ metric.value }}</span>
            <span class="mini-stat__label">{{ metric.label }}</span>
          </div>
        </div>
        <p v-if="!pluginOnline" class="mt-3 text-xs text-muted">TPS/RAM/аптайм появятся, когда заработает BydloBridge.</p>
      </section>

      <section class="mc-panel">
        <div class="section-head !mb-3">
          <BlIcon name="bolt" :size="14" tone="gold" />
          <p class="label-caps !mb-0">Управление сервером</p>
        </div>
        <textarea
          v-model="announceText"
          class="w-full rounded-sm border-2 border-[var(--line)] bg-[#0d0e13] p-3 text-sm outline-none focus:border-gold/30"
          placeholder="Текст объявления на сервер"
          rows="3"
        />
        <div class="mt-3 grid grid-cols-2 gap-2">
          <Button variant="blue" @click="announce">Объявление</Button>
          <Button v-if="store.profile?.is_head_admin" variant="red" @click="restartOpen = true">Рестарт</Button>
        </div>
      </section>



      <div v-if="alerts.length" class="space-y-2">

        <RouterLink

          v-for="alert in alerts"

          :key="alert.to + alert.label"

          :to="alert.to"

          class="status-banner pressable"

          :class="alert.tone"

        >

          <BlIcon :name="alert.icon" :size="16" tone="gold" />

          <div>

            <p class="font-bold">{{ alert.label }}</p>

            <p class="mt-0.5 text-xs opacity-90">{{ alert.hint }}</p>

          </div>

        </RouterLink>

      </div>



      <div class="grid grid-cols-2 gap-2">

        <StatCard label="Пользователи" :value="stats.users ?? 0" />

        <StatCard label="Привязано" :value="stats.linked ?? 0" />

        <StatCard label="Репорты" :value="stats.reports_new ?? 0" />

        <StatCard label="Inbox" :value="stats.inbox_new ?? 0" />

        <StatCard label="Whitelist" :value="stats.whitelist_pending ?? 0" />

        <StatCard label="Онлайн" :value="stats.online ?? 0" />

      </div>



      <section v-if="recentReports.length">

        <div class="section-head">

          <BlIcon name="report" :size="14" tone="gold" />

          <p class="label-caps !mb-0">Новые репорты</p>

        </div>

        <div class="menu-grid">

          <RouterLink

            v-for="item in recentReports"

            :key="item.id"

            to="/admin/inbox?kind=report"

            class="news-card pressable block"

          >

            <div class="flex items-start justify-between gap-2">

              <p class="font-bold">#{{ item.id }}</p>

              <span class="chip chip--gold">{{ item.category || "other" }}</span>

            </div>

            <p v-if="item.offender_nick" class="mt-1 text-xs text-muted">Нарушитель: {{ item.offender_nick }}</p>

            <p class="news-card__body !mt-2">{{ item.text }}</p>

          </RouterLink>

        </div>

      </section>



      <section>

        <div class="section-head">

          <BlIcon name="bolt" :size="14" tone="gold" />

          <p class="label-caps !mb-0">Быстрые действия</p>

        </div>

        <div class="action-grid">

          <RouterLink

            v-for="action in quickActions"

            :key="action.to"

            :to="action.to"

            class="action-tile pressable"

            :class="`action-tile--${action.tone}`"

          >

            <div class="action-tile__head">

              <div class="action-tile__icon">

                <BlIcon :name="action.icon" :size="20" tone="gold" />

              </div>

              <span v-if="action.badge" class="chip chip--live">{{ action.badge }}</span>

            </div>

            <div>

              <p class="action-tile__title">{{ action.label }}</p>

              <p class="action-tile__hint">{{ action.hint }}</p>

            </div>

          </RouterLink>

        </div>

      </section>



      <section>

        <div class="section-head">

          <BlIcon name="admin" :size="14" tone="gold" />

          <p class="label-caps !mb-0">Разделы</p>

        </div>

        <div class="menu-grid">

          <RouterLink

            v-for="link in adminLinks"

            :key="link.to"

            class="list-row pressable"

            :to="link.to"

          >

            <span class="list-row__main">

              <span class="icon-box icon-box--gold h-10 w-10">

                <BlIcon :name="link.icon" :size="18" tone="gold" />

              </span>

              {{ link.label }}

            </span>

            <BlIcon name="chevron" :size="14" tone="muted" />

          </RouterLink>

        </div>

      </section>

    </div>

    <Modal :open="restartOpen" title="Перезапуск сервера" text="Вы уверены? Доступно только head_admin." @close="restartOpen = false">
      <Button variant="red" @click="restart">Подтвердить</Button>
      <Button variant="ghost" @click="restartOpen = false">Отмена</Button>
    </Modal>
  </AppLayout>

</template>



<script setup lang="ts">

import { computed, onMounted, ref } from "vue";

import type { IconName } from "../../components/ui/BlIcon.vue";

import AppLayout from "../../layouts/AppLayout.vue";

import Navbar from "../../components/ui/Navbar.vue";

import BlIcon from "../../components/ui/BlIcon.vue";

import ServerHero from "../../components/ui/ServerHero.vue";

import StatCard from "../../components/ui/StatCard.vue";
import Button from "../../components/ui/Button.vue";
import Modal from "../../components/ui/Modal.vue";

import Loader from "../../components/ui/Loader.vue";

import ErrorState from "../../components/ui/ErrorState.vue";

import { api } from "../../api/client";
import { formatUptime } from "../../services/format";

import { useAppStore } from "../../stores/app";

import type { ServerStatus } from "../../types";



type RecentReport = {

  id: number;

  text: string;

  category?: string;

  offender_nick?: string | null;

};



type DashboardStats = {

  users?: number;

  linked?: number;

  online?: number;

  reports_new?: number;

  suggestions_new?: number;

  ideas_new?: number;

  inbox_new?: number;

  whitelist_pending?: number;

  server?: ServerStatus;

  recent_reports?: RecentReport[];

};



const store = useAppStore();

const loading = ref(true);
const error = ref("");
const stats = ref<DashboardStats>({});
const announceText = ref("");
const restartOpen = ref(false);



const serverStatus = computed(() => stats.value.server || store.server);
const recentReports = computed(() => stats.value.recent_reports || []);

const pluginOnline = computed(() => {
  const s = serverStatus.value;
  return Boolean(s?.tps != null || s?.ram || s?.uptime_seconds);
});

const serverMetrics = computed(() => {
  const s = serverStatus.value;
  if (!s) return [];
  return [
    { label: "TPS", value: s.tps != null ? String(s.tps) : "—" },
    { label: "RAM", value: s.ram || "—" },
    { label: "Аптайм", value: formatUptime(s.uptime_seconds) },
  ];
});



const alerts = computed(() => {

  const items: { to: string; label: string; hint: string; tone: string; icon: IconName }[] = [];

  if ((stats.value.reports_new ?? 0) > 0) {

    items.push({
      to: "/admin/inbox?kind=report",
      label: `${stats.value.reports_new} новых репортов`,

      hint: "Нужна реакция администрации",

      tone: "status-banner--error",

      icon: "report",

    });

  }

  if ((stats.value.inbox_new ?? 0) > 0) {

    items.push({

      to: "/admin/inbox",

      label: `${stats.value.inbox_new} предложений и идей`,

      hint: "Inbox ждёт просмотра",

      tone: "status-banner--warn",

      icon: "idea",

    });

  }

  if ((stats.value.whitelist_pending ?? 0) > 0) {

    items.push({

      to: "/admin/players",

      label: `${stats.value.whitelist_pending} без whitelist`,

      hint: "Игроки привязаны, но не добавлены",

      tone: "status-banner--warn",

      icon: "whitelist",

    });

  }

  return items;

});



const quickActions = computed(() => {

  const items: { to: string; icon: IconName; label: string; hint: string; tone: "purple" | "green" | "blue" | "red"; badge?: string }[] = [
    { to: "/admin/inbox", icon: "report", label: "Inbox", hint: "Репорты и идеи", tone: "red", badge: stats.value.inbox_new ? String(stats.value.inbox_new) : undefined },
    { to: "/admin/players", icon: "players", label: "Игроки", hint: "Поиск и карточка", tone: "purple" },

    { to: "/admin/links", icon: "link", label: "Привязки", hint: "Перенос аккаунтов", tone: "green" },

  ];

  return items;

});



const adminLinks = computed(() => {

  const links: { to: string; icon: IconName; label: string }[] = [

    { to: "/admin/inbox", icon: "idea", label: "Inbox" },

    { to: "/admin/news", icon: "news", label: "Новости" },

    { to: "/admin/builds", icon: "build", label: "Сборки" },

  ];

  if (store.profile?.is_head_admin) {

    links.push({ to: "/admin/staff", icon: "admin", label: "Администраторы" });

  }

  return links;

});



async function load() {

  loading.value = true;

  error.value = "";

  try {

    await store.bootstrap();

    stats.value = (await api.adminStats()) as DashboardStats;

  } catch (err) {

    error.value = err instanceof Error ? err.message : "Нет доступа";

  } finally {

    loading.value = false;

  }

}



onMounted(load);

async function announce() {
  if (!announceText.value.trim()) {
    store.showToast("Введите текст объявления");
    return;
  }
  await api.adminAnnounce(announceText.value.trim());
  store.showToast("Объявление отправлено");
  announceText.value = "";
}

async function restart() {
  await api.adminRestart();
  restartOpen.value = false;
  store.showToast("Перезапуск отправлен");
}

</script>


