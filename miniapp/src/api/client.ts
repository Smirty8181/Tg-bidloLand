const initData = () => window.Telegram?.WebApp?.initData || "";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers || {});
  headers.set("Content-Type", "application/json");
  const data = initData();
  if (data) headers.set("X-Telegram-Init-Data", data);
  const response = await fetch(path, { ...init, headers });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = (payload as { detail?: string }).detail || "Не удалось загрузить данные.";
    throw new Error(typeof detail === "string" ? detail : "Не удалось загрузить данные.");
  }
  return payload as T;
}

export const api = {
  bootstrap: () => request("/api/bootstrap"),
  me: () => request("/api/me"),
  profile: () => request("/api/profile"),
  status: () => request("/api/server/status"),
  players: () => request("/api/server/players"),
  playerProfile: (nickname: string) => request(`/api/players/${encodeURIComponent(nickname)}`),
  map: () => request<{ url: string }>("/api/map"),
  inventory: (player?: string) => request(`/api/inventory${player ? `?player=${encodeURIComponent(player)}` : ""}`),
  builds: () => request("/api/builds"),
  news: () => request("/api/news"),
  reports: () => request("/api/reports"),
  suggestions: () => request("/api/suggestions"),
  ideas: () => request("/api/ideas"),
  link: (nickname: string, force = false) =>
    request(force ? "/api/profile/link/force" : "/api/profile/link", {
      method: "POST",
      body: JSON.stringify({ nickname }),
    }),
  linkCheck: (nickname: string) =>
    request(`/api/profile/link/check?nickname=${encodeURIComponent(nickname)}`),
  linkCode: (body: { nickname?: string } = {}) =>
    request("/api/profile/link-code", { method: "POST", body: JSON.stringify(body) }),
  linkWatch: () => request<{ linked: boolean; nickname?: string; uuid?: string }>("/api/profile/link/watch"),
  whitelist: () => request("/api/whitelist", { method: "POST", body: "{}" }),
  createReport: (body: Record<string, unknown>) => request("/api/reports", { method: "POST", body: JSON.stringify(body) }),
  createSuggestion: (text: string) => request("/api/suggestions", { method: "POST", body: JSON.stringify({ text }) }),
  createIdea: (category: string, text: string) =>
    request("/api/ideas", { method: "POST", body: JSON.stringify({ category, text }) }),
  adminStats: () => request("/api/admin/stats"),
  adminReports: () => request("/api/admin/reports"),
  adminSuggestions: () => request("/api/admin/suggestions"),
  adminIdeas: () => request("/api/admin/ideas"),
  adminSearch: (q: string) => request(`/api/admin/players/search?q=${encodeURIComponent(q)}`),
  adminPlayerDetail: (nickname: string) => request(`/api/admin/players/${encodeURIComponent(nickname)}`),
  adminInbox: (params?: { kind?: string; status?: string }) => {
    const query = new URLSearchParams();
    if (params?.kind) query.set("kind", params.kind);
    if (params?.status) query.set("status", params.status);
    const suffix = query.toString() ? `?${query}` : "";
    return request(`/api/admin/inbox${suffix}`);
  },
  adminPunish: (body: Record<string, unknown>) => request("/api/admin/punish", { method: "POST", body: JSON.stringify(body) }),
  adminUpdateReport: (id: number, body: Record<string, unknown>) =>
    request(`/api/admin/reports/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  adminUpdateSuggestion: (id: number, body: Record<string, unknown>) =>
    request(`/api/admin/suggestions/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  adminUpdateIdea: (id: number, body: Record<string, unknown>) =>
    request(`/api/admin/ideas/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  adminAnnounce: (message: string) =>
    request("/api/admin/server/announce", { method: "POST", body: JSON.stringify({ message }) }),
  adminRestart: () => request("/api/admin/server/restart", { method: "POST", body: "{}" }),
  adminNewsCreate: (title: string, text: string) =>
    request("/api/admin/news", { method: "POST", body: JSON.stringify({ title, text }) }),
  adminNewsDelete: (id: number) => request(`/api/admin/news/${id}`, { method: "DELETE" }),
  adminBuilds: (body: Record<string, unknown>) => request("/api/admin/builds", { method: "POST", body: JSON.stringify(body) }),
  adminAdmins: () => request("/api/admin/admins"),
  adminRoles: (telegram_id: number, role: string) =>
    request("/api/admin/roles", { method: "POST", body: JSON.stringify({ telegram_id, role }) }),
  adminPunishments: (nick?: string) =>
    request(`/api/admin/punishments${nick ? `?nick=${encodeURIComponent(nick)}` : ""}`),
  adminLinkHistory: () => request("/api/admin/link/history"),
  adminLinkTransfer: (telegram_id: number, nickname: string) =>
    request("/api/admin/link/transfer", { method: "POST", body: JSON.stringify({ telegram_id, nickname }) }),
};
