<template>
  <AppLayout>
    <Navbar subtitle="Новости" />
    <input v-model="title" class="mb-2 w-full rounded-2xl bg-white/5 px-4 py-3" placeholder="Заголовок" />
    <textarea v-model="text" class="mb-3 w-full rounded-2xl bg-white/5 px-4 py-3" rows="4" placeholder="Текст новости" />
    <Button @click="create">📢 Создать новость</Button>
    <div class="mt-4 space-y-3">
      <article v-for="item in items" :key="item.id" class="news-card page-enter">
        <p class="font-display">{{ item.title }}</p>
        <p class="mt-2 text-sm text-[var(--muted)]">{{ item.text }}</p>
        <button class="mt-2 text-xs text-red-300" @click="remove(item.id)">Удалить</button>
      </article>
    </div>
  </AppLayout>
</template>
<script setup lang="ts">
import { onMounted, ref } from "vue";
import AppLayout from "../../layouts/AppLayout.vue";
import Navbar from "../../components/ui/Navbar.vue";
import Button from "../../components/ui/Button.vue";
import { api } from "../../api/client";
const title = ref("");
const text = ref("");
const items = ref<any[]>([]);
async function load() {
  items.value = ((await api.news()) as any).items || [];
}
async function create() {
  await api.adminNewsCreate(title.value, text.value);
  title.value = "";
  text.value = "";
  await load();
}
async function remove(id: number) {
  await api.adminNewsDelete(id);
  await load();
}
onMounted(load);
</script>
