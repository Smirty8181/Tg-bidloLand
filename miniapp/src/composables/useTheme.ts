import { onMounted } from "vue";

function applyThemeParams() {
  const webapp = window.Telegram?.WebApp;
  const tp = webapp?.themeParams;
  if (!tp) return;

  const root = document.documentElement;
  if (tp.bg_color) {
    root.style.setProperty("--bg", tp.bg_color);
    webapp?.setBackgroundColor(tp.bg_color);
  }
  if (tp.secondary_bg_color) {
    root.style.setProperty("--panel", tp.secondary_bg_color);
    root.style.setProperty("--bg-elevated", tp.secondary_bg_color);
    root.style.setProperty("--glass", `${tp.secondary_bg_color}bb`);
  }
  if (tp.text_color) root.style.setProperty("--text", tp.text_color);
  if (tp.hint_color) root.style.setProperty("--muted", tp.hint_color);
  if (tp.link_color) root.style.setProperty("--blue", tp.link_color);
  if (tp.button_color) root.style.setProperty("--gold", tp.button_color);
  if (tp.button_text_color) root.style.setProperty("--gold-soft", tp.button_text_color);

  const header = tp.bg_color || tp.secondary_bg_color || "#050810";
  webapp?.setHeaderColor(header);
}

export function useTheme() {
  onMounted(() => {
    applyThemeParams();
    window.Telegram?.WebApp?.onEvent?.("themeChanged", applyThemeParams);
  });
  return { applyThemeParams };
}
