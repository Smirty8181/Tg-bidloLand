<template>
  <AppLayout>
    <Navbar subtitle="Репорты" />
    <div v-if="counts" class="count-row mb-4">
      <div class="count-pill count-pill--red">
        <span class="count-pill__value">{{ counts.new }}</span>
        <span class="count-pill__label">Новых</span>
      </div>
      <div class="count-pill count-pill--gold">
        <span class="count-pill__value">{{ counts.in_review }}</span>
        <span class="count-pill__label">В работе</span>
      </div>
      <div class="count-pill count-pill--green">
        <span class="count-pill__value">{{ counts.resolved }}</span>
        <span class="count-pill__label">Решено</span>
      </div>
    </div>
    <div class="page-stack page-enter">
      <article v-for="item in items" :key="item.id" class="news-card">
        <div class="flex justify-between gap-2 text-sm">
          <b>#{{ item.id }}</b>
          <span class="ticket-status" :class="`ticket-status--${item.status}`">{{ statusLabel(item.status) }}</span>
        </div>
        <p v-if="item.offender_nick || item.category" class="mt-2 text-xs uppercase tracking-wide text-muted">
          {{ item.category || "other" }}{{ item.offender_nick ? ` · ${item.offender_nick}` : "" }}
        </p>
        <p class="mt-2 text-sm leading-relaxed">{{ item.text }}</p>
        <div v-if="item.attachments?.length" class="mt-3 flex flex-wrap gap-2">
          <span v-for="att in item.attachments" :key="att.id" class="attachment-chip">
            {{ att.kind }} #{{ att.id }}
          </span>
        </div>
        <div class="mt-3 flex flex-wrap gap-2">
          <button class="text-xs text-gold" @click="update(item.id, 'in_review')">В работу</button>
          <button class="text-xs text-emerald-300" @click="update(item.id, 'resolved')">Решить</button>
          <button class="text-xs text-red-300" @click="update(item.id, 'rejected')">Отклонить</button>
        </div>
      </article>
    </div>
  </AppLayout>
</template>
<script setup lang="ts">
import { onMounted, ref } from "vue";
import AppLayout from "../../layouts/AppLayout.vue";
import Navbar from "../../components/ui/Navbar.vue";
import { api } from "../../api/client";
import { statusLabel } from "../../services/format";
import { usePageRefresh } from "../../composables/usePageRefresh";
import type { TicketItem } from "../../types";

const items = ref<TicketItem[]>([]);
const counts = ref<any>(null);

async function load() {
  const data = (await api.adminReports()) as any;
  items.value = data.items || [];
  counts.value = data.counts;
}

usePageRefresh(load);

async function update(id: number, status: string) {
  await api.adminUpdateReport(id, { status });
  await load();
}

onMounted(load);
</script>

<style scoped>
.ticket-status {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.attachment-chip {
  display: inline-flex;
  padding: 4px 8px;
  border-radius: 8px;
  border: 1px solid var(--line);
  font-size: 10px;
  font-weight: 700;
}
</style>
