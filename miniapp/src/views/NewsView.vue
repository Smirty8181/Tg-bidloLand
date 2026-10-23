<template>
  <AppLayout>
    <Navbar subtitle="Новости БыдлоЛенда" refreshable :refreshing="loading" @refresh="load" />
    <Loader v-if="loading" />
    <EmptyState v-else-if="!items.length" title="Новостей пока нет" icon="news" text="Когда админы что-то опубликуют — появится здесь." />
    <div v-else class="page-stack page-enter stagger">
      <article v-for="item in items" :key="item.id" class="news-card">
        <div class="section-head !mb-2">
          <BlIcon name="news" :size="14" tone="gold" />
          <p class="news-card__title !mb-0">{{ item.title }}</p>
        </div>
        <p class="news-card__body">{{ item.text }}</p>
        <p class="news-card__date">{{ formatDate(item.created_at) }}</p>
      </article>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import AppLayout from "../layouts/AppLayout.vue";
import Navbar from "../components/ui/Navbar.vue";
import BlIcon from "../components/ui/BlIcon.vue";
import Loader from "../components/ui/Loader.vue";
import EmptyState from "../components/ui/EmptyState.vue";
import { api } from "../api/client";
import { formatDate } from "../services/format";
import type { NewsItem } from "../types";

const loading = ref(true);
const items = ref<NewsItem[]>([]);

async function load() {
  loading.value = true;
  try {
    const data = (await api.news()) as { items: NewsItem[] };
    items.value = data.items || [];
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>
