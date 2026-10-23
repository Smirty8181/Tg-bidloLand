<template>
  <section class="panel-glow server-hero">
    <div class="server-hero__inner">
      <p class="label-caps server-hero__eyebrow">Статус сервера</p>

      <div class="server-hero__top">
        <div class="server-hero__info">
          <p class="server-hero__players">
            {{ status.count ?? 0 }}<span>/{{ status.max ?? 20 }}</span>
          </p>
          <p class="server-hero__label">игроков на БыдлоЛенде</p>
          <p v-if="status.motd || status.name" class="server-hero__motd">{{ status.motd || status.name }}</p>
        </div>
        <div class="avatar-frame server-hero__logo-wrap">
          <img src="/logo.jpg" class="avatar-frame__inner" alt="" />
        </div>
      </div>

      <div class="server-hero__ip-block">
        <div class="server-hero__ip-text">
          <span class="server-hero__ip-value">{{ primaryAddress }}</span>
          <span v-if="secondaryAddress" class="server-hero__ip-alias">{{ secondaryAddress }}</span>
        </div>
        <button type="button" class="server-hero__copy-btn pressable" @click="copyAddress">
          <BlIcon name="link" :size="14" tone="gold" />
          {{ copied ? "Скопировано" : "Копировать" }}
        </button>
      </div>

      <div class="server-hero__footer">
        <BlIcon name="server" :size="14" tone="muted" />
        <span class="server-hero__footer-label">Версия сервера</span>
        <span class="server-hero__footer-value">{{ shortVersion(status.version) }}</span>
      </div>

      <div v-if="isAdmin && adminStats.length" class="server-hero__admin">
        <div v-for="stat in adminStats" :key="stat.label" class="server-hero__admin-item">
          <span class="server-hero__admin-label">{{ stat.label }}</span>
          <span class="server-hero__admin-value">{{ stat.value }}</span>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import BlIcon from "./BlIcon.vue";
import { formatUptime } from "../../services/format";
import type { ServerStatus } from "../../types";
import { useTelegram } from "../../composables/useTelegram";

const props = withDefaults(defineProps<{ status: ServerStatus; isAdmin?: boolean }>(), { isAdmin: false });
const copied = ref(false);
const { haptic } = useTelegram();

const primaryAddress = computed(() => {
  const s = props.status;
  const host = s.address?.split(":")[0];
  if (host && !/^\d+\.\d+\.\d+\.\d+$/.test(host)) return host;
  return s.address_anycast?.split(":")[0] || s.address_alias?.split(":")[0] || s.address || "—";
});

const secondaryAddress = computed(() => {
  const s = props.status;
  if (s.address && s.address !== primaryAddress.value) return s.address;
  if (s.address_alias && s.address_alias !== primaryAddress.value) return s.address_alias;
  return null;
});

const copyText = computed(() => props.status.address_anycast || props.status.address || props.status.address_alias || primaryAddress.value);

const adminStats = computed(() => {
  if (!props.isAdmin) return [];
  const s = props.status;
  const rows = [
    { label: "TPS", value: s.tps != null ? String(s.tps) : "—" },
    { label: "RAM", value: s.ram || "—" },
    { label: "CPU", value: s.cpu_percent != null ? `${s.cpu_percent}%` : "—" },
  ];
  if (s.uptime_seconds) rows.push({ label: "Аптайм", value: formatUptime(s.uptime_seconds) });
  return rows;
});

function shortVersion(value?: string | null) {
  if (!value) return "Paper 1.21.10";
  return value.replace("Paper ", "Paper ");
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
.server-hero {
  border-radius: var(--radius-lg);
}

.server-hero__inner {
  position: relative;
  padding: 16px;
  border-radius: inherit;
  background: var(--panel);
}

.server-hero__eyebrow {
  margin: 0 0 12px;
  color: #7a849a;
}

.server-hero__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.server-hero__players {
  margin: 0;
  font-family: Unbounded, Manrope, sans-serif;
  font-size: 2.25rem;
  font-weight: 800;
  line-height: 1;
  color: var(--gold-soft);
}

.server-hero__players span {
  font-size: 1.15rem;
  color: var(--muted);
  font-weight: 700;
}

.server-hero__label {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--muted);
}

.server-hero__motd {
  margin: 4px 0 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.45);
}

.server-hero__logo-wrap {
  width: 72px;
  height: 72px;
  flex-shrink: 0;
}

.server-hero__logo-wrap .avatar-frame__inner {
  width: 68px;
  height: 68px;
}

.server-hero__ip-block {
  margin-top: 16px;
  padding: 14px;
  border-radius: var(--radius-md);
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--line);
}

.server-hero__ip-value {
  display: block;
  font-family: Unbounded, Manrope, sans-serif;
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  word-break: break-all;
}

.server-hero__ip-alias {
  display: block;
  margin-top: 4px;
  font-size: 11px;
  color: var(--muted);
  word-break: break-all;
}

.server-hero__copy-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid rgba(232, 176, 32, 0.35);
  background: rgba(232, 176, 32, 0.08);
  color: var(--gold-soft);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  cursor: pointer;
}

.server-hero__footer {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--line);
}

.server-hero__footer-label {
  flex: 1;
  font-size: 11px;
  font-weight: 600;
  color: var(--muted);
}

.server-hero__footer-value {
  font-size: 12px;
  font-weight: 800;
  color: var(--text);
}

.server-hero__admin {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-top: 12px;
}

.server-hero__admin-item {
  padding: 8px;
  border-radius: 10px;
  border: 1px solid var(--line);
  background: rgba(0, 0, 0, 0.2);
  text-align: center;
}

.server-hero__admin-label {
  display: block;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--muted);
}

.server-hero__admin-value {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  font-weight: 800;
}
</style>
