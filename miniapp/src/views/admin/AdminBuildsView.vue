<template>
  <AppLayout>
    <Navbar subtitle="Сборки" />
    <div class="space-y-4">
      <Card v-for="platform in ['windows', 'zip']" :key="platform">
        <p class="font-display">{{ platform }}</p>
        <input v-model="forms[platform].url" class="mt-2 w-full rounded-xl bg-white/5 px-3 py-2 text-sm" placeholder="URL" />
        <input v-model="forms[platform].file_size" class="mt-2 w-full rounded-xl bg-white/5 px-3 py-2 text-sm" placeholder="Размер" />
        <Button class="mt-3" @click="save(platform)">Сохранить</Button>
      </Card>
    </div>
  </AppLayout>
</template>
<script setup lang="ts">
import { reactive } from "vue";
import AppLayout from "../../layouts/AppLayout.vue";
import Navbar from "../../components/ui/Navbar.vue";
import Card from "../../components/ui/Card.vue";
import Button from "../../components/ui/Button.vue";
import { api } from "../../api/client";
import { useAppStore } from "../../stores/app";
const store = useAppStore();
const forms = reactive<Record<string, { url: string; file_size: string }>>({
  windows: { url: "", file_size: "" },
  zip: { url: "", file_size: "" },
});
async function save(platform: string) {
  await api.adminBuilds({ platform, ...forms[platform], version: "1.21.10", name: platform });
  store.showToast("Ссылка обновлена");
}
</script>
