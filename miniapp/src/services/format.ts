export function statusLabel(status: string) {
  const map: Record<string, string> = {
    new: "Новый",
    in_review: "Рассматривается",
    resolved: "Решён",
    rejected: "Отклонён",
    accepted: "Принято",
  };
  return map[status] || status;
}

export function statusTone(status: string): "ok" | "warn" | "bad" | "info" {
  if (status === "resolved" || status === "accepted") return "ok";
  if (status === "rejected") return "bad";
  if (status === "in_review") return "info";
  return "warn";
}

export function formatDate(value?: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" });
}

export function formatUptime(seconds?: number | null) {
  if (!seconds || seconds < 1) return "—";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 24) {
    const d = Math.floor(h / 24);
    return `${d}д ${h % 24}ч`;
  }
  if (h > 0) return `${h}ч ${m}м`;
  return `${m}м`;
}

export function itemLabel(item: { custom_name?: string | null; name?: string | null; material: string }) {
  return item.custom_name || item.name || item.material.replaceAll("_", " ");
}

export const ideaCategories = [
  { id: "plugin", label: "Плагин" },
  { id: "mechanic", label: "Механика" },
  { id: "pvp", label: "PvP" },
  { id: "build", label: "Строительство" },
  { id: "event", label: "Ивент" },
  { id: "races", label: "Расы" },
  { id: "other", label: "Другое" },
];
