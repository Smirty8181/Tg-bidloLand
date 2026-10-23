<template>
  <AppLayout>
    <Navbar subtitle="Сборка БыдлоЛенда" />
    <div class="page-stack page-enter stagger">
      <section class="mc-panel mc-panel--gold sub-hero">
        <div class="flex items-center gap-3">
          <div class="menu-tile__icon icon-box--gold">
            <BlIcon name="build" :size="22" tone="gold" />
          </div>
          <div>
            <p class="sub-hero__title">Сборка БыдлоЛенда</p>
            <p class="sub-hero__desc">Minecraft {{ version }}</p>
          </div>
        </div>
        <p class="sub-hero__desc mt-3">Рекомендуемая сборка для игры на сервере — с модами и настройками под наш мир.</p>
      </section>

      <section>
        <div class="section-head">
          <BlIcon name="build" :size="14" tone="gold" />
          <p class="label-caps !mb-0">Скачать</p>
        </div>
        <div class="menu-grid">
          <a v-for="item in items" :key="item.platform" :href="item.url || undefined" target="_blank" class="block">
            <div
              class="menu-tile menu-tile--stack pressable"
              :class="item.platform === 'windows' ? 'menu-tile--gold' : 'menu-tile--blue'"
            >
              <div class="menu-tile__icon">
                <BlIcon name="build" :size="20" tone="gold" />
              </div>
              <p class="menu-tile__label">{{ item.platform === "windows" ? "Windows" : "ZIP архив" }}</p>
              <p class="menu-tile__hint">
                {{ item.url ? (item.file_size || "Скачать") : "Скоро" }}
              </p>
            </div>
          </a>
        </div>
      </section>

      <Card>
        <p class="label-caps mb-3">Инструкция</p>
        <p class="whitespace-pre-line text-sm leading-relaxed text-muted">{{ instruction }}</p>
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
import type { BuildItem } from "../types";

const items = ref<BuildItem[]>([]);
const version = ref("1.21.10");
const instruction = ref("Скачай сборку, установи Minecraft 1.21.10 и распакуй моды из архива.");

onMounted(async () => {
  const data = (await api.builds()) as { version: string; items: BuildItem[] };
  items.value = data.items || [];
  version.value = data.version;
  instruction.value = items.value[0]?.instruction || instruction.value;
});
</script>
