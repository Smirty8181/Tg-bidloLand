<template>
  <AppLayout>
    <Navbar :subtitle="title" :refreshing="store.refreshing" />
    <div class="mb-4 flex gap-2">
      <button type="button" class="mc-btn mc-btn--gold pressable" @click="open = true">
        <BlIcon name="report" :size="16" tone="gold" />
        Создать
      </button>
    </div>
    <Loader v-if="loading" />
    <ErrorState v-else-if="error" :text="error" @retry="load" />
    <EmptyState v-else-if="!items.length" :title="emptyTitle" :text="emptyHint" :icon="emptyIcon" />
    <div v-else class="page-stack page-enter stagger">
      <article v-for="item in items" :key="item.id" class="news-card">
        <div class="flex items-start justify-between gap-2">
          <div>
            <p class="font-display font-bold">#{{ item.id }}</p>
            <p v-if="item.category || item.offender_nick" class="mt-1 text-[11px] uppercase tracking-wide text-muted">
              {{ categoryLabel(item.category) }}{{ item.offender_nick ? ` · ${item.offender_nick}` : "" }}
            </p>
          </div>
          <span class="ticket-status" :class="`ticket-status--${item.status}`">{{ statusLabel(item.status) }}</span>
        </div>
        <p class="mt-3 text-sm leading-relaxed">{{ item.text }}</p>
        <div v-if="item.attachments?.length" class="mt-3 flex flex-wrap gap-2">
          <span v-for="att in item.attachments" :key="att.id" class="attachment-chip">
            <BlIcon :name="attachmentIcon(att.kind)" :size="12" tone="gold" />
            {{ attachmentLabel(att.kind) }}
            <span v-if="att.caption" class="text-muted">· {{ att.caption }}</span>
          </span>
        </div>
        <p v-if="item.admin_comment" class="mt-3 rounded-xl border border-gold/20 bg-gold/5 p-3 text-sm text-gold">
          Ответ админа: {{ item.admin_comment }}
        </p>
        <p class="mt-3 text-xs text-muted">{{ formatDate(item.created_at) }}</p>
      </article>
    </div>

    <Modal :open="open" :title="modalTitle" @close="open = false">
      <div v-if="mode === 'ideas'" class="grid grid-cols-2 gap-2">
        <button
          v-for="cat in ideaCategories"
          :key="cat.id"
          type="button"
          class="category-chip pressable"
          :class="category === cat.id ? 'category-chip--active' : ''"
          @click="category = cat.id"
        >
          {{ cat.label }}
        </button>
      </div>
      <div v-if="mode === 'reports'" class="grid grid-cols-2 gap-2">
        <button
          v-for="cat in reportCategories"
          :key="cat.id"
          type="button"
          class="category-chip pressable"
          :class="category === cat.id ? 'category-chip--active' : ''"
          @click="category = cat.id"
        >
          {{ cat.label }}
        </button>
      </div>
      <input
        v-if="mode === 'reports'"
        v-model="offender"
        class="mc-input mt-3"
        placeholder="Ник нарушителя (необязательно)"
      />
      <textarea v-model="text" rows="5" class="mc-input mt-3 resize-none" :placeholder="placeholder" />
      <p class="mt-2 text-xs text-muted">Минимум 8 символов. Сейчас: {{ text.trim().length }}</p>
      <p v-if="mode === 'reports'" class="mt-2 text-xs text-muted">Скриншоты можно прикрепить через бота командой /report</p>
      <button type="button" class="mc-btn mc-btn--gold mt-3 w-full pressable" :disabled="busy || !canSubmit" @click="submit">
        {{ busy ? "Отправка..." : "Отправить" }}
      </button>
    </Modal>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import type { IconName } from "../components/ui/BlIcon.vue";
import AppLayout from "../layouts/AppLayout.vue";
import Navbar from "../components/ui/Navbar.vue";
import BlIcon from "../components/ui/BlIcon.vue";
import Loader from "../components/ui/Loader.vue";
import ErrorState from "../components/ui/ErrorState.vue";
import EmptyState from "../components/ui/EmptyState.vue";
import Modal from "../components/ui/Modal.vue";
import { api } from "../api/client";
import { formatDate, ideaCategories, statusLabel } from "../services/format";
import type { TicketItem } from "../types";
import { useAppStore } from "../stores/app";
import { usePageRefresh } from "../composables/usePageRefresh";

const props = defineProps<{ mode: "reports" | "suggestions" | "ideas" }>();
const store = useAppStore();

const reportCategories = [
  { id: "cheat", label: "Читы" },
  { id: "grief", label: "Гриф" },
  { id: "chat", label: "Чат" },
  { id: "other", label: "Другое" },
];

const title =
  props.mode === "reports" ? "Мои репорты" : props.mode === "ideas" ? "Мои идеи" : "Мои предложения";
const modalTitle =
  props.mode === "reports" ? "Новый репорт" : props.mode === "ideas" ? "Новая идея" : "Новое предложение";
const emptyTitle =
  props.mode === "reports" ? "Репортов пока нет" : props.mode === "ideas" ? "Идей пока нет" : "Предложений пока нет";
const emptyHint =
  props.mode === "reports"
    ? "Нажми «Создать», чтобы отправить жалобу администрации."
    : "Нажми «Создать», чтобы предложить улучшение сервера.";
const emptyIcon: IconName = props.mode === "reports" ? "report" : props.mode === "ideas" ? "idea" : "news";
const placeholder =
  props.mode === "reports"
    ? "Опишите нарушение: что произошло, где, когда"
    : "Опишите идею или предложение подробнее";

const loading = ref(true);
const error = ref("");
const items = ref<TicketItem[]>([]);
const open = ref(false);
const text = ref("");
const offender = ref("");
const category = ref("other");
const busy = ref(false);

const canSubmit = computed(() => text.value.trim().length >= 8);

function categoryLabel(value?: string | null) {
  return reportCategories.find((c) => c.id === value)?.label || value || "";
}

function attachmentIcon(kind: string): IconName {
  if (kind === "photo") return "profile";
  if (kind === "video") return "players";
  return "report";
}

function attachmentLabel(kind: string) {
  if (kind === "photo") return "Фото";
  if (kind === "video") return "Видео";
  if (kind === "document") return "Файл";
  return kind;
}

async function load() {
  loading.value = true;
  error.value = "";
  try {
    await store.bootstrap();
    const fn = props.mode === "reports" ? api.reports : props.mode === "ideas" ? api.ideas : api.suggestions;
    const data = (await fn()) as { items: TicketItem[] };
    items.value = data.items || [];
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Ошибка";
  } finally {
    loading.value = false;
  }
}

usePageRefresh(load);

async function submit() {
  if (!canSubmit.value) {
    store.showToast("Нужно минимум 8 символов");
    return;
  }
  busy.value = true;
  try {
    if (props.mode === "reports") {
      await api.createReport({ text: text.value.trim(), offender_nick: offender.value.trim() || undefined, category: category.value });
    } else if (props.mode === "ideas") {
      await api.createIdea(category.value, text.value.trim());
    } else {
      await api.createSuggestion(text.value.trim());
    }
    open.value = false;
    text.value = "";
    offender.value = "";
    store.showToast("Отправлено администрации");
    await load();
  } catch (err) {
    store.showToast(err instanceof Error ? err.message : "Ошибка");
  } finally {
    busy.value = false;
  }
}

onMounted(load);
</script>

<style scoped>
.ticket-status {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 4px 8px;
  border: 1px solid var(--line);
  border-radius: 8px;
  white-space: nowrap;
}
.ticket-status--open,
.ticket-status--new {
  color: #7dffb0;
}
.ticket-status--in_progress,
.ticket-status--in_review {
  color: var(--gold);
}
.ticket-status--closed,
.ticket-status--resolved,
.ticket-status--rejected {
  color: #ff8a8a;
}

.attachment-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 10px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.03);
  font-size: 11px;
  font-weight: 700;
}
</style>
