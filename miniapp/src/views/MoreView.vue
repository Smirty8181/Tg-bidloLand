<template>
  <AppLayout>
    <Navbar subtitle="Ещё" refreshable :refreshing="store.refreshing" @refresh="refresh" />

    <div class="page-stack page-enter stagger">
      <section v-for="group in groups" :key="group.title">
        <div class="section-head">
          <BlIcon :name="group.icon" :size="14" tone="gold" />
          <p class="label-caps !mb-0">{{ group.title }}</p>
        </div>
        <div class="menu-grid" :class="group.grid ? 'menu-grid--2' : ''">
          <RouterLink
            v-for="item in group.items"
            :key="item.to"
            :to="item.to"
            class="menu-tile pressable"
            :class="[group.grid ? 'menu-tile--stack' : '', `menu-tile--${item.tone}`]"
          >
            <div class="menu-tile__icon">
              <BlIcon :name="item.icon" :size="20" tone="gold" />
            </div>
            <div :class="group.grid ? '' : 'min-w-0 flex-1'">
              <p class="menu-tile__label">{{ item.label }}</p>
              <p v-if="item.hint" class="menu-tile__hint">{{ item.hint }}</p>
            </div>
            <BlIcon v-if="!group.grid" name="chevron" :size="14" tone="muted" />
          </RouterLink>
        </div>
      </section>

      <RouterLink
        v-if="store.profile?.is_admin"
        to="/admin"
        class="feature-banner menu-tile menu-tile--gold pressable"
      >
        <div class="menu-tile__icon">
          <BlIcon name="admin" :size="22" tone="gold" />
        </div>
        <div class="min-w-0 flex-1">
          <p class="menu-tile__label text-gold">Админ-панель</p>
          <p class="menu-tile__hint">Репорты, наказания, сервер</p>
        </div>
        <BlIcon name="chevron" :size="14" tone="gold" />
      </RouterLink>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import type { IconName } from "../components/ui/BlIcon.vue";
import AppLayout from "../layouts/AppLayout.vue";
import Navbar from "../components/ui/Navbar.vue";
import BlIcon from "../components/ui/BlIcon.vue";
import { useAppStore, clearBootstrapCache } from "../stores/app";
import { useTelegram } from "../composables/useTelegram";

const store = useAppStore();
const { haptic } = useTelegram();

onMounted(() => store.bootstrap());

async function refresh() {
  haptic("light");
  clearBootstrapCache();
  await store.bootstrap();
}

type MenuItem = {
  to: string;
  icon: IconName;
  label: string;
  hint?: string;
  tone: "purple" | "green" | "blue" | "red" | "gold";
};

const groups: { title: string; icon: IconName; grid?: boolean; items: MenuItem[] }[] = [
  {
    title: "Игра",
    icon: "chest",
    grid: true,
    items: [
      { to: "/map", icon: "map", label: "Карта", hint: "Dynmap", tone: "blue" },
      { to: "/build", icon: "build", label: "Сборка", hint: "Моды", tone: "green" },
      { to: "/whitelist", icon: "whitelist", label: "Whitelist", hint: "Доступ", tone: "gold" },
      { to: "/link", icon: "link", label: "Привязка", hint: "Minecraft", tone: "purple" },
    ],
  },
  {
    title: "Сообщество",
    icon: "news",
    items: [
      { to: "/news", icon: "news", label: "Новости", hint: "Объявления сервера", tone: "gold" },
      { to: "/reports", icon: "report", label: "Репорт", hint: "Жалоба на игрока", tone: "red" },
      { to: "/suggestions", icon: "idea", label: "Предложение", hint: "Улучшения", tone: "blue" },
      { to: "/ideas", icon: "idea", label: "Идея", hint: "Новые механики", tone: "purple" },
    ],
  },
];
</script>
