<template>
  <AppLayout>
    <Navbar subtitle="Администраторы" />
    <div class="space-y-3">
      <article v-for="item in items" :key="item.telegram_id" class="news-card page-enter">
        <p>{{ item.username || item.telegram_id }}</p>
        <p class="text-xs text-[var(--muted)]">{{ item.role }}</p>
      </article>
    </div>
    <input v-model="telegramId" class="mt-4 w-full rounded-2xl bg-white/5 px-4 py-3" placeholder="Telegram ID" />
    <input v-model="role" class="mt-2 w-full rounded-2xl bg-white/5 px-4 py-3" placeholder="player / admin / head_admin" />
    <Button class="mt-3" @click="save">Назначить роль</Button>
  </AppLayout>
</template>
<script setup lang="ts">
import { onMounted, ref } from "vue";
import AppLayout from "../../layouts/AppLayout.vue";
import Navbar from "../../components/ui/Navbar.vue";
import Button from "../../components/ui/Button.vue";
import { api } from "../../api/client";
const items = ref<any[]>([]);
const telegramId = ref("");
const role = ref("admin");
async function load() {
  items.value = ((await api.adminAdmins()) as any).items || [];
}
async function save() {
  await api.adminRoles(Number(telegramId.value), role.value);
  await load();
}
onMounted(load);
</script>
