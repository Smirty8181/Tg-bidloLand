<template>
  <AppLayout>
    <Navbar subtitle="Привязка Minecraft" :refreshing="store.refreshing" />

    <div class="space-y-4 stagger page-enter">
      <LinkOnboarding v-if="!isLinked" :linked="false" :dismissible="false" hide-cta />

      <section class="gradient-border link-hero mc-panel--gold">
        <div class="link-bridge">
          <div class="link-bridge__node">
            <SkinAvatar size="md" :nickname="linkedNick" />
            <span class="text-[11px] font-bold text-muted">Minecraft</span>
            <span class="max-w-[90px] truncate text-xs font-extrabold">{{ linkedNick || "—" }}</span>
          </div>
          <div class="link-bridge__pulse">
            <div class="link-bridge__line w-full min-w-[48px]" />
          </div>
          <div class="link-bridge__node">
            <div class="avatar-frame">
              <img src="/logo.jpg" alt="" class="avatar-frame__inner h-14 w-14 object-cover" />
            </div>
            <span class="text-[11px] font-bold text-muted">Telegram</span>
            <span class="max-w-[90px] truncate text-xs font-extrabold">{{ tgLabel }}</span>
          </div>
        </div>
        <p class="mt-4 text-center text-sm leading-relaxed text-muted">
          Свяжи аккаунты — откроются <span class="text-gold">инвентарь</span>, whitelist и профиль на сервере.
        </p>
      </section>

      <div v-if="isLinked" class="status-banner status-banner--ok">
        <BlIcon name="online" :size="16" tone="gold" />
        <div>
          <p class="font-bold">Аккаунт привязан</p>
          <p class="mt-1 opacity-90">{{ linkedNick }} ↔ @{{ store.profile?.username || store.profile?.telegram_id }}</p>
        </div>
      </div>

      <div v-if="polling" class="status-banner status-banner--warn">
        <BlIcon name="link" :size="16" tone="gold" />
        <p>Ожидаем команду /link на сервере…</p>
      </div>

      <Card accent>
        <SegmentTabs v-model="mode" :tabs="modes" />

        <div v-if="mode === 'direct'" class="mt-5 space-y-4">
          <div>
            <label class="label-caps mb-2 block">Minecraft-ник</label>
            <div class="mc-input-wrap">
              <span class="mc-input-wrap__icon"><BlIcon name="profile" :size="16" tone="muted" /></span>
              <input
                v-model="nick"
                maxlength="16"
                class="mc-input"
                placeholder="Smirty_228"
                autocapitalize="off"
                autocomplete="off"
                @input="scheduleCheck"
              />
            </div>
          </div>

          <div v-if="nickStatus" class="status-banner" :class="statusClass">
            <BlIcon :name="statusIcon" :size="16" tone="gold" />
            <p>{{ nickStatus.message }}</p>
          </div>

          <SkinAvatar v-if="nick.trim().length >= 3" class="mx-auto" size="xl" :nickname="nick.trim()" />

          <Button :disabled="busy || !canSubmit" @click="link(false)">
            {{ isLinked && !needsForce ? "Обновить" : needsForce ? "Сменить ник" : "Привязать" }}
          </Button>

          <Button
            v-if="nickStatus?.can_reclaim && store.profile?.is_head_admin"
            variant="red"
            :disabled="busy || !nick.trim()"
            @click="link(true)"
          >
            Перехватить (head admin)
          </Button>
        </div>

        <div v-else class="mt-5 space-y-4">
          <p class="text-sm leading-relaxed text-muted">
            Получи код, зайди на сервер и введи команду в чат — привязка произойдёт автоматически.
          </p>

          <Button :disabled="busy" @click="generateCode">
            {{ linkCode ? "Новый код" : "Получить код" }}
          </Button>

          <div v-if="linkCode" class="space-y-3">
            <div class="code-box">
              <div>
                <p class="label-caps text-gold/80">Команда</p>
                <p class="code-box__value mt-1">{{ linkCommand }}</p>
              </div>
              <Button size="sm" variant="ghost" @click="copyCommand">{{ copied ? "✓" : "Copy" }}</Button>
            </div>
            <p class="text-center text-xs text-muted">Истекает через {{ expiresLabel }}</p>
          </div>
        </div>
      </Card>

      <Card>
        <p class="label-caps mb-3">Пошагово</p>
        <ol class="space-y-3">
          <li v-for="(step, i) in steps" :key="step" class="flex gap-3 text-sm text-muted">
            <span class="chip chip--gold shrink-0">{{ i + 1 }}</span>
            <span class="leading-relaxed">{{ step }}</span>
          </li>
        </ol>
      </Card>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import type { IconName } from "../components/ui/BlIcon.vue";
import AppLayout from "../layouts/AppLayout.vue";
import Navbar from "../components/ui/Navbar.vue";
import Card from "../components/ui/Card.vue";
import Button from "../components/ui/Button.vue";
import BlIcon from "../components/ui/BlIcon.vue";
import SkinAvatar from "../components/ui/SkinAvatar.vue";
import SegmentTabs from "../components/ui/SegmentTabs.vue";
import { api } from "../api/client";
import LinkOnboarding from "../components/ui/LinkOnboarding.vue";
import { useAppStore, clearBootstrapCache } from "../stores/app";
import { useTelegram } from "../composables/useTelegram";
import { usePageRefresh } from "../composables/usePageRefresh";

type LinkCheck = {
  ok: boolean;
  state: "invalid" | "linked" | "taken" | "change" | "available";
  message: string;
  can_reclaim?: boolean;
};

type LinkCodeResp = {
  code: string;
  command: string;
  expires_in: number;
  instruction: string;
};

const store = useAppStore();
const { haptic, success, fail } = useTelegram();

const nick = ref("");
const busy = ref(false);
const mode = ref("direct");
const nickStatus = ref<LinkCheck | null>(null);
const linkCode = ref("");
const linkCommand = ref("");
const expiresAt = ref(0);
const copied = ref(false);
const polling = ref(false);
let checkTimer: number | undefined;
let countdownTimer: number | undefined;
let pollTimer: number | undefined;

const modes = [
  { id: "direct", label: "По нику", icon: "link" as IconName },
  { id: "code", label: "Через /link", icon: "profile" as IconName },
];

const steps = [
  "Открой Mini App именно с того Telegram, который хочешь привязать.",
  "Введи свой Minecraft-ник и нажми «Привязать» — или получи код для команды /link на сервере.",
  "После привязки обнови профиль: появятся инвентарь, whitelist и статистика.",
];

const linkedNick = computed(() => store.profile?.minecraft?.nickname || null);
const isLinked = computed(() => Boolean(linkedNick.value));
const tgLabel = computed(() => (store.profile?.username ? `@${store.profile.username}` : `ID ${store.profile?.telegram_id ?? "—"}`));
const needsForce = computed(() => nickStatus.value?.state === "change" || nickStatus.value?.state === "taken");
const canSubmit = computed(() => Boolean(nick.trim()) && nickStatus.value?.state !== "invalid" && nickStatus.value?.state !== "taken");

const statusClass = computed(() => {
  const s = nickStatus.value?.state;
  if (s === "linked" || s === "available") return "status-banner--ok";
  if (s === "change" || s === "taken") return "status-banner--warn";
  return "status-banner--error";
});

const statusIcon = computed((): IconName => {
  const s = nickStatus.value?.state;
  if (s === "linked" || s === "available") return "online";
  if (s === "change") return "link";
  return "offline";
});

const expiresLabel = computed(() => {
  const left = Math.max(0, expiresAt.value - Date.now());
  const m = Math.floor(left / 60000);
  const s = Math.floor((left % 60000) / 1000);
  return `${m}:${String(s).padStart(2, "0")}`;
});

function scheduleCheck() {
  window.clearTimeout(checkTimer);
  checkTimer = window.setTimeout(runCheck, 350);
}

async function runCheck() {
  const value = nick.value.trim();
  if (value.length < 3) {
    nickStatus.value = null;
    return;
  }
  try {
    nickStatus.value = (await api.linkCheck(value)) as LinkCheck;
  } catch {
    nickStatus.value = { ok: false, state: "invalid", message: "Не удалось проверить ник." };
  }
}

async function refreshProfile() {
  haptic("light");
  clearBootstrapCache();
  await store.bootstrap();
  if (linkedNick.value) nick.value = linkedNick.value;
  await runCheck();
}

usePageRefresh(refreshProfile);

async function link(force: boolean) {
  busy.value = true;
  try {
    await api.link(nick.value.trim(), force || needsForce.value);
    success();
    clearBootstrapCache();
    await store.bootstrap();
    nickStatus.value = { ok: true, state: "linked", message: "✅ Привязано! Проверь сообщение от бота в Telegram." };
  } catch (err) {
    fail();
    nickStatus.value = {
      ok: false,
      state: "taken",
      message: err instanceof Error ? err.message : "Ошибка привязки",
    };
  } finally {
    busy.value = false;
  }
}

async function generateCode() {
  busy.value = true;
  try {
    const body = nick.value.trim() ? { nickname: nick.value.trim() } : {};
    const data = (await api.linkCode(body)) as LinkCodeResp;
    linkCode.value = data.code;
    linkCommand.value = data.command || `/link ${data.code}`;
    expiresAt.value = Date.now() + (data.expires_in || 900) * 1000;
    startCountdown();
    startPolling();
    haptic("light");
  } catch (err) {
    nickStatus.value = {
      ok: false,
      state: "invalid",
      message: err instanceof Error ? err.message : "Не удалось создать код",
    };
  } finally {
    busy.value = false;
  }
}

async function pollLinkStatus() {
  if (!linkCode.value || isLinked.value) {
    stopPolling();
    return;
  }
  try {
    const data = await api.linkWatch();
    if (data.linked) {
      stopPolling();
      linkCode.value = "";
      success();
      clearBootstrapCache();
      await store.bootstrap();
      store.showToast(`Привязан: ${data.nickname}`);
    }
  } catch {
    /* ignore transient errors while polling */
  }
}

function startPolling() {
  stopPolling();
  polling.value = true;
  pollTimer = window.setInterval(pollLinkStatus, 3000);
  pollLinkStatus();
}

function stopPolling() {
  polling.value = false;
  if (pollTimer) window.clearInterval(pollTimer);
  pollTimer = undefined;
}

async function copyCommand() {
  if (!linkCommand.value) return;
  try {
    await navigator.clipboard.writeText(linkCommand.value);
    copied.value = true;
    haptic("light");
    success();
    window.setTimeout(() => {
      copied.value = false;
    }, 2000);
  } catch {
    fail();
  }
}

function startCountdown() {
  window.clearInterval(countdownTimer);
  countdownTimer = window.setInterval(() => {
    if (Date.now() >= expiresAt.value) {
      linkCode.value = "";
      stopPolling();
      window.clearInterval(countdownTimer);
    }
  }, 1000);
}

watch(mode, () => {
  haptic("light");
  if (mode.value !== "code") stopPolling();
  else if (linkCode.value) startPolling();
});

onMounted(async () => {
  await store.bootstrap();
  if (linkedNick.value) {
    nick.value = linkedNick.value;
    await runCheck();
  }
});

onUnmounted(() => {
  window.clearTimeout(checkTimer);
  window.clearInterval(countdownTimer);
  stopPolling();
});
</script>
