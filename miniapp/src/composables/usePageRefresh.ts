import { inject, onMounted, onUnmounted, provide, type InjectionKey } from "vue";
import { useAppStore } from "../stores/app";

type RefreshFn = () => Promise<void>;

const PAGE_REFRESH_KEY: InjectionKey<(fn: RefreshFn | null) => void> = Symbol("pageRefresh");
export const APP_REFRESH_KEY: InjectionKey<() => Promise<void>> = Symbol("appRefresh");

export function providePageRefresh() {
  let handler: RefreshFn | null = null;
  const store = useAppStore();

  const register = (fn: RefreshFn | null) => {
    handler = fn;
  };

  provide(PAGE_REFRESH_KEY, register);
  provide(APP_REFRESH_KEY, refresh);

  async function refresh() {
    store.refreshing = true;
    try {
      if (handler) await handler();
      else await store.bootstrap();
    } finally {
      store.refreshing = false;
    }
  }

  return { refresh, register };
}

export function usePageRefresh(fn: RefreshFn) {
  const register = inject(PAGE_REFRESH_KEY);
  onMounted(() => register?.(fn));
  onUnmounted(() => register?.(null));
}
