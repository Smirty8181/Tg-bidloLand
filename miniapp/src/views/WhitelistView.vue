<template>
  <AppLayout>
    <Navbar subtitle="Whitelist" />

    <div class="page-stack page-enter stagger">
      <section class="mc-panel mc-panel--gold sub-hero text-center">
        <div class="menu-tile__icon icon-box--gold mx-auto">
          <BlIcon name="whitelist" :size="24" tone="gold" />
        </div>
        <p class="sub-hero__title mt-4">Whitelist</p>
        <p class="stat-value mt-2 text-xl font-bold">{{ store.profile?.minecraft?.nickname || "не привязан" }}</p>
        <div class="mt-4 flex items-center justify-center gap-2">
          <span class="chip" :class="store.profile?.minecraft?.is_whitelisted ? 'chip--live' : ''">
            <BlIcon :name="store.profile?.minecraft?.is_whitelisted ? 'online' : 'offline'" :size="10" />
            {{ store.profile?.minecraft?.is_whitelisted ? "Добавлен" : "Не добавлен" }}
          </span>
        </div>
      </section>

      <div v-if="!store.profile?.minecraft" class="status-banner status-banner--warn">
        <BlIcon name="link" :size="16" tone="gold" />
        <p>Сначала привяжи Minecraft-аккаунт в разделе «Привязка».</p>
      </div>

      <Card>
        <p class="text-sm leading-relaxed text-muted">
          Whitelist ограничивает доступ к серверу. После привязки ника нажми кнопку ниже — администрация получит запрос на добавление.
        </p>
        <button
          type="button"
          class="mc-btn mc-btn--gold mt-5 w-full pressable"
          :disabled="busy || !store.profile?.minecraft"
          @click="add"
        >
          {{ busy ? "Добавляем..." : "Добавить в whitelist" }}
        </button>
      </Card>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import AppLayout from "../layouts/AppLayout.vue";
import Navbar from "../components/ui/Navbar.vue";
import Card from "../components/ui/Card.vue";
import BlIcon from "../components/ui/BlIcon.vue";
import { api } from "../api/client";
import { useAppStore } from "../stores/app";

const store = useAppStore();
const busy = ref(false);
onMounted(() => store.bootstrap());

async function add() {
  busy.value = true;
  try {
    const result = (await api.whitelist()) as { result: string; nickname: string };
    store.showToast(result.result === "already" ? "Уже в whitelist" : `Ник ${result.nickname} добавлен`);
    await store.bootstrap();
  } catch (err) {
    store.showToast(err instanceof Error ? err.message : "Ошибка");
  } finally {
    busy.value = false;
  }
}
</script>
