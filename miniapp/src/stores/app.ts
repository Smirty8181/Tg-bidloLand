import { defineStore } from "pinia";

import { ref } from "vue";

import { api } from "../api/client";

import type { ServerAlert, ServerStatus, UserProfile } from "../types";

const CACHE_PREFIX = "bydloland.bootstrap.v1";

type BootstrapCache = {
  profile: UserProfile;
  server: ServerStatus;
  savedAt: number;
  telegramId?: number;
};

function currentTelegramId(): number | null {
  const id = window.Telegram?.WebApp?.initDataUnsafe?.user?.id;
  return typeof id === "number" ? id : null;
}

function cacheKey(): string {
  const tgId = currentTelegramId();
  return tgId ? `${CACHE_PREFIX}.${tgId}` : CACHE_PREFIX;
}

function readCache(): BootstrapCache | null {
  try {
    const raw = localStorage.getItem(cacheKey());
    if (!raw) return null;
    const data = JSON.parse(raw) as BootstrapCache;
    if (!data?.profile || !data?.server) return null;
    const tgId = currentTelegramId();
    if (tgId && data.telegramId && data.telegramId !== tgId) return null;
    return data;
  } catch {
    return null;
  }
}

function writeCache(profile: UserProfile, server: ServerStatus) {
  try {
    const payload: BootstrapCache = {
      profile,
      server,
      savedAt: Date.now(),
      telegramId: profile.telegram_id,
    };
    localStorage.setItem(cacheKey(), JSON.stringify(payload));
  } catch {
    /* ignore quota errors */
  }
}

export function clearBootstrapCache() {
  try {
    const tgId = currentTelegramId();
    if (tgId) localStorage.removeItem(`${CACHE_PREFIX}.${tgId}`);
    localStorage.removeItem(CACHE_PREFIX);
  } catch {
    /* ignore */
  }
}

export const useAppStore = defineStore("app", () => {
  const profile = ref<UserProfile | null>(null);
  const server = ref<ServerStatus | null>(null);
  const loading = ref(false);
  const refreshing = ref(false);
  const error = ref("");
  const toast = ref("");
  const offline = ref(false);
  const cacheAge = ref<number | null>(null);

  async function bootstrap() {
    const cached = readCache();
    if (cached) {
      profile.value = cached.profile;
      server.value = cached.server;
      cacheAge.value = cached.savedAt;
      loading.value = !cached.profile.minecraft;
      refreshing.value = Boolean(cached.profile.minecraft);
    } else {
      loading.value = true;
    }
    error.value = "";
    try {
      const data = (await api.bootstrap()) as {
        profile: UserProfile;
        server: ServerStatus;
        alerts?: ServerAlert[];
      };
      profile.value = data.profile;
      server.value = data.server;
      writeCache(data.profile, data.server);
      cacheAge.value = Date.now();
      offline.value = false;
      for (const alert of data.alerts || []) {
        showToast(alert.message);
      }
    } catch (err) {
      if (cached) {
        offline.value = true;
        cacheAge.value = cached.savedAt;
      } else {
        error.value = err instanceof Error ? err.message : "Не удалось загрузить данные.";
      }
    } finally {
      loading.value = false;
      refreshing.value = false;
    }
  }

  function showToast(message: string) {
    toast.value = message;
    window.setTimeout(() => {
      if (toast.value === message) toast.value = "";
    }, 2800);
  }

  return { profile, server, loading, refreshing, error, toast, offline, cacheAge, bootstrap, showToast };
});
