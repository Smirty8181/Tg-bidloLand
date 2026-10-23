<template>
  <AppLayout>
    <Navbar subtitle="Привязки Minecraft" :refreshing="refreshing" />
    <Loader v-if="loading" />
    <div v-else class="space-y-4 page-enter">
      <Card accent>
        <p class="label-caps mb-3">Перенос привязки</p>
        <div class="space-y-3">
          <input v-model="telegramId" class="mc-input" inputmode="numeric" placeholder="Telegram ID" />
          <input v-model="nickname" class="mc-input" placeholder="Minecraft-ник" autocapitalize="off" />
          <Button :disabled="busy || !canTransfer" @click="transfer">Перенести на указанный TG</Button>
        </div>
      </Card>

      <Card>
        <p class="label-caps mb-3">История привязок</p>
        <EmptyState v-if="!items.length" title="Пока пусто" text="Здесь будут события link/unlink/transfer." icon="link" />
        <div v-else class="space-y-2">
          <article v-for="item in items" :key="item.id" class="history-row">
            <div class="flex items-center justify-between gap-2">
              <p class="font-bold">{{ item.nickname }}</p>
              <span class="history-action">{{ actionLabel(item.action) }}</span>
            </div>
            <p class="mt-1 text-xs text-muted">
              TG {{ item.telegram_id }}
              <span v-if="item.previous_telegram_id"> · было TG {{ item.previous_telegram_id }}</span>
              · {{ methodLabel(item.method) }}
            </p>
            <p class="mt-1 text-[11px] text-muted">{{ formatDate(item.created_at) }}</p>
          </article>
        </div>
      </Card>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import AppLayout from "../../layouts/AppLayout.vue";
import Navbar from "../../components/ui/Navbar.vue";
import Card from "../../components/ui/Card.vue";
import Button from "../../components/ui/Button.vue";
import Loader from "../../components/ui/Loader.vue";
import EmptyState from "../../components/ui/EmptyState.vue";
import { api } from "../../api/client";
import { formatDate } from "../../services/format";
import type { LinkHistoryItem } from "../../types";
import { useAppStore } from "../../stores/app";
import { usePageRefresh } from "../../composables/usePageRefresh";

const store = useAppStore();
const loading = ref(true);
const refreshing = ref(false);
const busy = ref(false);
const items = ref<LinkHistoryItem[]>([]);
const telegramId = ref("");
const nickname = ref("");

const canTransfer = computed(() => /^\d+$/.test(telegramId.value.trim()) && nickname.value.trim().length >= 3);

function actionLabel(action: string) {
  const map: Record<string, string> = {
    linked: "Привязка",
    relinked: "Смена",
    reclaimed: "Перехват",
    transferred: "Перенос",
  };
  return map[action] || action;
}

function methodLabel(method: string) {
  const map: Record<string, string> = { direct: "прямая", code: "/link", admin: "админ" };
  return map[method] || method;
}

async function loadHistory() {
  const data = (await api.adminLinkHistory()) as { items: LinkHistoryItem[] };
  items.value = data.items || [];
}

async function loadAll() {
  refreshing.value = true;
  try {
    await store.bootstrap();
    await loadHistory();
  } finally {
    refreshing.value = false;
    loading.value = false;
  }
}

usePageRefresh(loadAll);

async function transfer() {
  if (!canTransfer.value) return;
  busy.value = true;
  try {
    await api.adminLinkTransfer(Number(telegramId.value.trim()), nickname.value.trim());
    store.showToast("Привязка перенесена");
    telegramId.value = "";
    nickname.value = "";
    await loadHistory();
  } catch (err) {
    store.showToast(err instanceof Error ? err.message : "Ошибка переноса");
  } finally {
    busy.value = false;
  }
}

onMounted(loadAll);
</script>

<style scoped>
.history-row {
  padding: 12px;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.02);
}

.history-action {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--gold);
}
</style>
