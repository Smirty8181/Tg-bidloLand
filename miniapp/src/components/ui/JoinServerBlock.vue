<template>
  <section class="join-block mc-panel">
    <div class="section-head !mb-3">
      <BlIcon name="server" :size="14" tone="gold" />
      <p class="label-caps !mb-0">Как зайти на сервер</p>
    </div>

    <div class="join-block__row">
      <div class="min-w-0">
        <p class="join-block__label">IP адрес</p>
        <p class="join-block__value">{{ primaryAddress }}</p>
        <p v-if="secondaryAddress" class="join-block__alias">{{ secondaryAddress }}</p>
      </div>
      <button type="button" class="join-block__copy pressable" @click="copyAddress">
        <BlIcon name="link" :size="14" tone="gold" />
        {{ copied ? "OK" : "Копировать" }}
      </button>
    </div>

    <div class="join-block__meta">
      <div class="join-block__meta-item">
        <span class="join-block__meta-label">Версия</span>
        <span class="join-block__meta-value">{{ shortVersion(status?.version) }}</span>
      </div>
      <RouterLink to="/build" class="join-block__build pressable">
        <BlIcon name="build" :size="14" tone="gold" />
        Скачать сборку
      </RouterLink>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { RouterLink } from "vue-router";
import BlIcon from "./BlIcon.vue";
import type { ServerStatus } from "../../types";
import { useTelegram } from "../../composables/useTelegram";

const props = defineProps<{ status?: ServerStatus | null }>();
const copied = ref(false);
const { haptic } = useTelegram();

const primaryAddress = computed(() => {
  const s = props.status;
  if (!s) return "—";
  const host = s.address?.split(":")[0];
  if (host && !/^\d+\.\d+\.\d+\.\d+$/.test(host)) return host;
  return s.address_anycast?.split(":")[0] || s.address_alias?.split(":")[0] || s.address || "—";
});

const secondaryAddress = computed(() => {
  const s = props.status;
  if (!s) return null;
  if (s.address && s.address !== primaryAddress.value) return s.address;
  if (s.address_alias && s.address_alias !== primaryAddress.value) return s.address_alias;
  return null;
});

const copyText = computed(
  () => props.status?.address_anycast || props.status?.address || props.status?.address_alias || primaryAddress.value,
);

function shortVersion(value?: string | null) {
  if (!value) return "1.21.10";
  return value.replace("Paper ", "");
}

async function copyAddress() {
  const text = copyText.value;
  if (!text || text === "—") return;
  try {
    await navigator.clipboard.writeText(text);
    copied.value = true;
    haptic("light");
    window.setTimeout(() => {
      copied.value = false;
    }, 1800);
  } catch {
    copied.value = false;
  }
}
</script>

<style scoped>
.join-block {
  padding: 14px 16px;
  border-radius: var(--radius-lg);
}

.join-block__row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  border-radius: var(--radius-md);
  background: rgba(0, 0, 0, 0.22);
  border: 1px solid var(--line);
}

.join-block__label {
  margin: 0;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}

.join-block__value {
  margin: 4px 0 0;
  font-family: Unbounded, Manrope, sans-serif;
  font-size: 14px;
  font-weight: 700;
  word-break: break-all;
}

.join-block__alias {
  margin: 4px 0 0;
  font-size: 11px;
  color: var(--muted);
  word-break: break-all;
}

.join-block__copy {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(232, 176, 32, 0.35);
  background: rgba(232, 176, 32, 0.08);
  color: var(--gold-soft);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.join-block__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--line);
}

.join-block__meta-label {
  display: block;
  font-size: 10px;
  color: var(--muted);
}

.join-block__meta-value {
  display: block;
  margin-top: 2px;
  font-size: 13px;
  font-weight: 800;
}

.join-block__build {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.03);
  font-size: 11px;
  font-weight: 700;
  color: var(--gold-soft);
  text-decoration: none;
}
</style>
