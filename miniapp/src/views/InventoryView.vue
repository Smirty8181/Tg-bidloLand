<template>
  <AppLayout>
    <Navbar subtitle="Инвентарь" />
    <Loader v-if="loading" />
    <ErrorState v-else-if="error" :text="error" @retry="load" />
    <EmptyState
      v-else-if="!data?.ok"
      :title="emptyTitle"
      :text="emptyText"
      icon="chest"
    >
      <RouterLink v-if="needsLink" to="/profile/link" class="mt-4 inline-flex items-center gap-2 text-sm font-bold text-gold">
        Привязать аккаунт
        <BlIcon name="chevron" :size="14" tone="gold" />
      </RouterLink>
    </EmptyState>
    <div v-else class="page-stack page-enter stagger">
      <section class="mc-panel mc-panel--gold p-4">
        <div class="flex items-center justify-between gap-3">
          <div class="flex items-center gap-2">
            <BlIcon name="chest" :size="20" tone="gold" />
            <p class="font-display text-lg font-bold">{{ data.player }}</p>
          </div>
          <span class="chip" :class="data.online ? 'chip--live' : ''">
            {{ data.online ? "В игре" : "Снимок" }}
          </span>
        </div>
        <p v-if="data.cached || data.online === false" class="mt-2 text-xs text-muted">
          Показан последний сохранённый инвентарь. Зайди на сервер для обновления.
        </p>
      </section>

      <section class="mc-panel p-4">
        <p class="label-caps mb-3">Броня</p>
        <div class="inv-armor">
          <InventorySlot :item="armor.helmet" @click="select(armor.helmet)" />
          <InventorySlot :item="armor.chestplate" @click="select(armor.chestplate)" />
          <InventorySlot :item="armor.leggings" @click="select(armor.leggings)" />
          <InventorySlot :item="armor.boots" @click="select(armor.boots)" />
        </div>
        <div class="inv-grid mx-auto mt-4 max-w-full">
          <InventorySlot v-for="slot in 36" :key="slot" :item="bySlot[slot - 1]" @click="select(bySlot[slot - 1])" />
        </div>
      </section>

      <section v-if="selected" class="mc-panel p-4">
        <p class="font-display text-base font-bold">{{ itemLabel(selected) }}</p>
        <p class="mt-1 text-sm text-[var(--muted)]">Количество: {{ selected.amount }}</p>
        <p v-if="selected.enchantments?.length" class="mt-2 text-sm text-gold">
          {{ selected.enchantments.map((e) => `${e.id} ${e.level}`).join(", ") }}
        </p>
        <p v-if="selected.durability != null" class="mt-2 text-sm">
          Прочность: {{ selected.durability }}/{{ selected.max_durability }}
        </p>
      </section>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import AppLayout from "../layouts/AppLayout.vue";
import Navbar from "../components/ui/Navbar.vue";
import BlIcon from "../components/ui/BlIcon.vue";
import InventorySlot from "../components/ui/InventorySlot.vue";
import Loader from "../components/ui/Loader.vue";
import ErrorState from "../components/ui/ErrorState.vue";
import EmptyState from "../components/ui/EmptyState.vue";
import { api } from "../api/client";
import { itemLabel } from "../services/format";
import type { InventoryItem } from "../types";

type InventoryResponse = {
  ok: boolean;
  error?: string;
  message?: string;
  player?: string;
  online?: boolean;
  cached?: boolean;
  inventory?: InventoryItem[];
  armor?: Record<string, InventoryItem>;
};

const loading = ref(true);
const error = ref("");
const data = ref<InventoryResponse | null>(null);
const selected = ref<InventoryItem | null>(null);

const armor = computed(() => data.value?.armor || {});
const bySlot = computed<Record<number, InventoryItem>>(() => {
  const map: Record<number, InventoryItem> = {};
  for (const item of data.value?.inventory || []) map[item.slot] = item;
  return map;
});
const needsLink = computed(() => data.value?.error === "not_linked");
const emptyTitle = computed(() =>
  needsLink.value ? "Аккаунт не привязан" : "Инвентарь недоступен"
);
const emptyText = computed(
  () =>
    data.value?.message ||
    (needsLink.value
      ? "Привяжи Minecraft-ник в профиле, затем зайди на сервер."
      : "Зайди на сервер — инвентарь сохранится автоматически.")
);

function select(item?: InventoryItem | null) {
  if (item) selected.value = item;
}

async function load() {
  loading.value = true;
  error.value = "";
  selected.value = null;
  try {
    data.value = (await api.inventory()) as InventoryResponse;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Ошибка";
    data.value = null;
  } finally {
    loading.value = false;
  }
}
onMounted(load);
</script>
