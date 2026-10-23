<template>
  <AppLayout>
    <Navbar subtitle="Карточка игрока" />

    <Loader v-if="loading && !player" />
    <ErrorState v-else-if="error" :text="error" @retry="load" />

    <div v-else-if="player" class="page-stack page-enter">
      <section class="profile-hero mc-panel mc-panel--gold rounded-2xl p-5 text-center">
        <SkinAvatar size="xl" :nickname="player.nickname" :uuid="player.uuid" class="mx-auto" />
        <h1 class="mt-4 font-display text-xl font-bold">{{ player.nickname }}</h1>
        <p v-if="player.telegram_username" class="mt-1 text-sm text-muted">@{{ player.telegram_username }}</p>
        <div class="mt-3 flex flex-wrap justify-center gap-2">
          <span class="chip" :class="player.online ? 'chip--live' : ''">
            {{ player.online ? "В игре" : "Оффлайн" }}
          </span>
          <span class="chip" :class="player.is_whitelisted ? 'chip--live' : ''">
            {{ player.is_whitelisted ? "Whitelist ✓" : "Нет whitelist" }}
          </span>
          <span v-if="player.role" class="chip chip--gold">{{ player.role }}</span>
        </div>
      </section>

      <div class="grid grid-cols-2 gap-2 text-sm">
        <div class="mini-stat">
          <span class="mini-stat__label">Telegram ID</span>
          <span class="mini-stat__value !text-sm">{{ player.telegram_id ?? "—" }}</span>
        </div>
        <div class="mini-stat">
          <span class="mini-stat__label">K/D</span>
          <span class="mini-stat__value !text-sm">{{ player.kd ?? 0 }}</span>
        </div>
      </div>

      <section v-if="player.last_report" class="news-card">
        <p class="label-caps">Последний репорт</p>
        <p class="mt-2 text-xs text-muted">#{{ player.last_report.id }} · {{ statusLabel(player.last_report.status) }}</p>
        <p class="mt-2 text-sm">{{ player.last_report.text }}</p>
      </section>

      <section v-if="player.punishments?.length" class="news-card">
        <p class="label-caps">Наказания</p>
        <div v-for="p in player.punishments" :key="p.id" class="mt-2 text-xs text-muted">
          {{ p.type }} · {{ p.reason }}
        </div>
      </section>

      <div class="grid grid-cols-2 gap-2">
        <Button variant="ghost" @click="punish('kick')">👢 Кик</Button>
        <Button variant="ghost" @click="punish('mute')">🔇 Мут</Button>
        <Button variant="red" @click="punish('ban')">🔨 Бан</Button>
        <Button variant="ghost" @click="punish('warning')">⚠️ Варн</Button>
      </div>
    </div>

    <Modal :open="confirm.open" title="Подтверждение" :text="confirm.text" @close="confirm.open = false">
      <Button variant="red" @click="apply">Подтвердить</Button>
      <Button variant="ghost" @click="confirm.open = false">Отмена</Button>
    </Modal>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";
import AppLayout from "../../layouts/AppLayout.vue";
import Navbar from "../../components/ui/Navbar.vue";
import Button from "../../components/ui/Button.vue";
import Modal from "../../components/ui/Modal.vue";
import SkinAvatar from "../../components/ui/SkinAvatar.vue";
import Loader from "../../components/ui/Loader.vue";
import ErrorState from "../../components/ui/ErrorState.vue";
import { api } from "../../api/client";
import { statusLabel } from "../../services/format";
import { useAppStore } from "../../stores/app";

const route = useRoute();
const store = useAppStore();
const loading = ref(true);
const error = ref("");
const player = ref<any>(null);
const confirm = reactive({ open: false, text: "", payload: null as any });

async function load() {
  loading.value = true;
  error.value = "";
  try {
    player.value = await api.adminPlayerDetail(String(route.params.nick || ""));
  } catch (err) {
    player.value = null;
    error.value = err instanceof Error ? err.message : "Не найден";
  } finally {
    loading.value = false;
  }
}

function punish(type: string) {
  if (!player.value?.nickname) return;
  confirm.payload = {
    target_nick: player.value.nickname,
    type,
    reason: "Наказание из Mini App",
    duration_seconds: type === "kick" || type === "warning" ? null : 86400,
  };
  confirm.text = `${type.toUpperCase()} ${player.value.nickname}?`;
  confirm.open = true;
}

async function apply() {
  await api.adminPunish(confirm.payload);
  confirm.open = false;
  store.showToast("Наказание применено");
  await load();
}

watch(() => route.params.nick, load);
onMounted(load);
</script>
