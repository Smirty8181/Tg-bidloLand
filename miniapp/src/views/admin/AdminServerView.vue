<template>
  <AppLayout>
    <Navbar subtitle="Управление сервером" />
    <ServerHero v-if="store.server" :status="store.server" :is-admin="true" class="mb-3" />
    <Card>
      <div class="flex items-center gap-2">
        <BlIcon name="server" :size="18" tone="gold" />
        <p class="font-display text-base font-bold">Управление</p>
      </div>
      <p v-if="store.server?.panel_url" class="mt-3 truncate text-xs text-[var(--muted)]">
        Панель: {{ store.server.panel_url }}
      </p>
      <textarea
        v-model="message"
        class="mt-4 w-full rounded-sm border-2 border-[var(--line)] bg-[#0d0e13] p-3 text-sm outline-none focus:border-gold/30"
        placeholder="Текст объявления на сервер"
      />
      <div class="mt-3 space-y-2">
        <Button @click="store.bootstrap()">
          <BlIcon name="refresh" :size="14" tone="gold" class="inline" />
          Обновить
        </Button>
        <Button variant="blue" @click="announce">Объявление</Button>
        <Button v-if="store.profile?.is_head_admin" variant="red" @click="open = true">Перезапуск</Button>
      </div>
    </Card>
    <Modal :open="open" title="Перезапуск сервера" text="Вы уверены? Доступно только head_admin." @close="open = false">
      <Button variant="red" @click="restart">Подтвердить</Button>
      <Button variant="ghost" @click="open = false">Отмена</Button>
    </Modal>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import AppLayout from "../../layouts/AppLayout.vue";
import Navbar from "../../components/ui/Navbar.vue";
import Card from "../../components/ui/Card.vue";
import Button from "../../components/ui/Button.vue";
import BlIcon from "../../components/ui/BlIcon.vue";
import ServerHero from "../../components/ui/ServerHero.vue";
import Modal from "../../components/ui/Modal.vue";
import { api } from "../../api/client";
import { useAppStore } from "../../stores/app";

const store = useAppStore();
const message = ref("");
const open = ref(false);
onMounted(() => store.bootstrap());

async function announce() {
  await api.adminAnnounce(message.value);
  store.showToast("Объявление отправлено");
}
async function restart() {
  await api.adminRestart();
  open.value = false;
  store.showToast("Перезапуск отправлен");
}
</script>
