<template>
  <AppLayout>
    <Navbar subtitle="Игроки" />

    <div class="search-panel mc-input-wrap mb-3">
      <span class="mc-input-wrap__icon"><BlIcon name="players" :size="16" tone="muted" /></span>
      <input v-model="query" class="mc-input" placeholder="Ник или Telegram ID" @keyup.enter="search" />
    </div>
    <Button class="mb-4" @click="search">Найти</Button>

    <div class="page-stack page-enter">
      <RouterLink
        v-for="item in items"
        :key="item.telegram_id"
        :to="playerLink(item)"
        class="list-row pressable block"
      >
        <span class="list-row__main min-w-0">
          <SkinAvatar
            size="sm"
            :nickname="item.minecraft?.nickname"
            class="shrink-0"
          />
          <span class="min-w-0 truncate font-display">{{ item.minecraft?.nickname || item.username || item.telegram_id }}</span>
        </span>
        <BlIcon name="chevron" :size="14" tone="muted" />
      </RouterLink>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { RouterLink } from "vue-router";
import AppLayout from "../../layouts/AppLayout.vue";
import Navbar from "../../components/ui/Navbar.vue";
import Button from "../../components/ui/Button.vue";
import BlIcon from "../../components/ui/BlIcon.vue";
import SkinAvatar from "../../components/ui/SkinAvatar.vue";
import { api } from "../../api/client";

const query = ref("");
const items = ref<any[]>([]);

function playerLink(item: any) {
  const nick = item.minecraft?.nickname;
  if (nick) return `/admin/players/${encodeURIComponent(nick)}`;
  return "/admin/players";
}

async function search() {
  if (!query.value.trim()) return;
  const data = (await api.adminSearch(query.value.trim())) as any;
  items.value = data.items || [];
}
</script>
