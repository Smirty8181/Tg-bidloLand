const profile = {
  id: 0,
  telegram_id: 0,
  username: null,
  first_name: "Игрок примера",
  role: "player",
  is_admin: false,
  is_head_admin: false,
  minecraft: {
    nickname: "DemoCrafter",
    uuid: null,
    is_whitelisted: true,
    linked_at: "2026-01-01T12:00:00Z",
    playtime_seconds: 93600,
    kills: 18,
    deaths: 7,
    kd: 2.57,
    last_online: null,
  },
  online: true,
};

const server = {
  online: true,
  count: 2,
  max: 20,
  players: ["DemoCrafter", "PixelFox"],
  tps: 20,
  uptime: "3 дня",
  version: "Paper 1.21.10",
  name: "БыдлоЛенд — демо",
  address: "play.example.invalid",
};

const news = [{
  id: 1,
  title: "Добро пожаловать в демо",
  text: "Это статический предпросмотр интерфейса. Здесь используются только вымышленные примеры данных.",
  created_at: "2026-01-01T12:00:00Z",
}];

const inventoryItem = {
  slot: 0,
  material: "DIAMOND_PICKAXE",
  amount: 1,
  name: "Демо-кирка",
  enchantments: [{ id: "efficiency", level: 5 }],
  durability: 1500,
  max_durability: 1561,
};

const fixtures: Record<string, unknown> = {
  "/api/bootstrap": { profile, server, alerts: [] },
  "/api/me": profile,
  "/api/profile": profile,
  "/api/server/status": server,
  "/api/server/players": { ...server, players_hidden: false },
  "/api/map": { url: "" },
  "/api/inventory": {
    ok: true,
    player: "DemoCrafter",
    online: false,
    cached: true,
    inventory: [inventoryItem],
    armor: {},
  },
  "/api/builds": {
    version: "1.21.10",
    items: [
      { id: 1, name: "Демо-сборка", platform: "windows", url: "", version: "1.21.10", file_size: "", instruction: "Демо-ссылка на скачивание отключена." },
      { id: 2, name: "Демо-архив", platform: "zip", url: "", version: "1.21.10", file_size: "", instruction: "Демо-ссылка на скачивание отключена." },
    ],
  },
  "/api/news": { items: news },
  "/api/reports": { items: [] },
  "/api/suggestions": { items: [] },
  "/api/ideas": { items: [] },
  "/api/profile/link/watch": { linked: true, nickname: "DemoCrafter" },
};

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

export async function demoRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = (init.method || "GET").toUpperCase();
  if (method !== "GET" && method !== "HEAD") {
    throw new Error("Демо-режим доступен только для чтения: отправка изменений отключена.");
  }
  if (path.startsWith("/api/admin")) {
    throw new Error("Административные функции недоступны в демо-режиме.");
  }

  const pathname = path.split("?")[0];
  if (pathname.startsWith("/api/players/")) {
    const nickname = decodeURIComponent(pathname.slice("/api/players/".length));
    if (server.players.includes(nickname)) {
      return clone({
        nickname,
        uuid: null,
        online: true,
        linked: false,
        is_whitelisted: true,
        kills: 4,
        deaths: 2,
        playtime_seconds: 36000,
        kd: 2,
        telegram_username: null,
      }) as T;
    }
    throw new Error("В демо-данных такой игрок не найден.");
  }
  if (pathname === "/api/profile/link/check") {
    return clone({ available: true, nickname: "DemoCrafter" }) as T;
  }
  if (pathname === "/api/inventory" || pathname.startsWith("/api/inventory?")) {
    return clone(fixtures["/api/inventory"]) as T;
  }
  if (pathname === "/api/admin" || pathname.startsWith("/api/admin/")) {
    throw new Error("Административные функции недоступны в демо-режиме.");
  }
  if (Object.prototype.hasOwnProperty.call(fixtures, pathname)) {
    return clone(fixtures[pathname]) as T;
  }
  throw new Error("Этот экран не представлен в статическом демо.");
}
