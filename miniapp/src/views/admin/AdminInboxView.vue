<template>
  <AppLayout>
    <Navbar subtitle="Inbox" refreshable :refreshing="loading" @refresh="load" />

    <Loader v-if="loading && !items.length" />
    <ErrorState v-else-if="error" :text="error" @retry="load" />

    <div v-else class="page-stack page-enter">
      <div v-if="counts" class="mini-stats">
        <div class="mini-stat">
          <span class="mini-stat__value">{{ counts.total_new ?? 0 }}</span>
          <span class="mini-stat__label">Новых</span>
        </div>
        <div class="mini-stat">
          <span class="mini-stat__value">{{ counts.report ?? 0 }}</span>
          <span class="mini-stat__label">Репорты</span>
        </div>
        <div class="mini-stat">
          <span class="mini-stat__value">{{ (counts.suggestion ?? 0) + (counts.idea ?? 0) }}</span>
          <span class="mini-stat__label">Идеи</span>
        </div>
      </div>

      <div class="flex flex-wrap gap-2">
        <button
          v-for="tab in kindTabs"
          :key="tab.id"
          class="chip pressable"
          :class="kindFilter === tab.id ? 'chip--gold' : ''"
          @click="setKind(tab.id)"
        >
          {{ tab.label }}
        </button>
      </div>

      <div class="flex flex-wrap gap-2">
        <button
          v-for="tab in statusTabs"
          :key="tab.id"
          class="chip pressable text-xs"
          :class="statusFilter === tab.id ? 'chip--live' : ''"
          @click="setStatus(tab.id)"
        >
          {{ tab.label }}
        </button>
      </div>

      <EmptyState
        v-if="!filtered.length"
        title="Пусто"
        :text="emptyText"
        icon="report"
      />

      <article v-for="item in filtered" :key="`${item.kind}-${item.id}`" class="news-card">
        <div class="flex items-start justify-between gap-2">
          <div>
            <p class="font-bold">#{{ item.id }}</p>
            <p class="mt-1 text-xs text-muted">{{ item.kind_label }} · {{ statusLabel(item.status) }}</p>
          </div>
          <span v-if="item.category" class="chip chip--gold">{{ item.category }}</span>
        </div>
        <p v-if="item.offender_nick" class="mt-2 text-xs text-muted">Нарушитель: {{ item.offender_nick }}</p>
        <p class="news-card__body !mt-2">{{ item.text }}</p>
        <div class="mt-3 flex flex-wrap gap-3 text-xs">
          <button class="text-gold" @click="setStatusFor(item, 'in_review')">В работу</button>
          <button class="text-emerald-300" @click="resolve(item)">Решить</button>
          <button class="text-red-300" @click="setStatusFor(item, 'rejected')">Отклонить</button>
        </div>
      </article>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import AppLayout from "../../layouts/AppLayout.vue";
import Navbar from "../../components/ui/Navbar.vue";
import Loader from "../../components/ui/Loader.vue";
import ErrorState from "../../components/ui/ErrorState.vue";
import EmptyState from "../../components/ui/EmptyState.vue";
import { api } from "../../api/client";
import { statusLabel } from "../../services/format";
import { useAppStore } from "../../stores/app";

type InboxItem = {
  id: number;
  kind: "report" | "suggestion" | "idea";
  kind_label: string;
  text: string;
  status: string;
  category?: string | null;
  offender_nick?: string | null;
};

const route = useRoute();
const router = useRouter();
const store = useAppStore();
const loading = ref(true);
const error = ref("");
const items = ref<InboxItem[]>([]);
const counts = ref<Record<string, number> | null>(null);
const kindFilter = ref(String(route.query.kind || "all"));
const statusFilter = ref(String(route.query.status || ""));

const kindTabs = [
  { id: "all", label: "Все" },
  { id: "report", label: "Репорты" },
  { id: "suggestion", label: "Предложения" },
  { id: "idea", label: "Идеи" },
];

const statusTabs = [
  { id: "", label: "Все статусы" },
  { id: "new", label: "Новые" },
  { id: "in_review", label: "В работе" },
  { id: "resolved", label: "Решённые" },
  { id: "accepted", label: "Принятые" },
  { id: "rejected", label: "Отклонённые" },
];

const filtered = computed(() => {
  let rows = items.value;
  if (kindFilter.value !== "all") {
    rows = rows.filter((i) => i.kind === kindFilter.value);
  }
  if (statusFilter.value) {
    rows = rows.filter((i) => i.status === statusFilter.value);
  }
  return rows;
});

const emptyText = computed(() =>
  kindFilter.value === "all" ? "Нет обращений по выбранным фильтрам." : "Нет записей в этой категории.",
);

function setKind(id: string) {
  kindFilter.value = id;
  router.replace({ query: { ...route.query, kind: id === "all" ? undefined : id } });
}

function setStatus(id: string) {
  statusFilter.value = id;
  router.replace({ query: { ...route.query, status: id || undefined } });
}

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const data = (await api.adminInbox({
      kind: kindFilter.value === "all" ? undefined : kindFilter.value,
      status: statusFilter.value || undefined,
    })) as any;
    items.value = data.items || [];
    counts.value = data.counts || null;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Ошибка";
  } finally {
    loading.value = false;
  }
}

async function setStatusFor(item: InboxItem, status: string) {
  if (item.kind === "report") await api.adminUpdateReport(item.id, { status });
  else if (item.kind === "suggestion") await api.adminUpdateSuggestion(item.id, { status });
  else await api.adminUpdateIdea(item.id, { status });
  store.showToast("Обновлено");
  await load();
}

async function resolve(item: InboxItem) {
  const status = item.kind === "report" ? "resolved" : "accepted";
  await setStatusFor(item, status);
}

watch([kindFilter, statusFilter], load);
onMounted(load);
</script>
