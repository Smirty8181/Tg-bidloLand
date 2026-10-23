export type Role = "player" | "admin" | "head_admin";

export interface MinecraftProfile {
  nickname: string;
  uuid?: string | null;
  is_whitelisted: boolean;
  linked_at?: string | null;
  playtime_seconds: number;
  kills: number;
  deaths: number;
  kd: number;
  last_online?: string | null;
}

export interface UserProfile {
  id: number;
  telegram_id: number;
  username?: string | null;
  first_name?: string | null;
  role: Role;
  is_admin: boolean;
  is_head_admin: boolean;
  minecraft: MinecraftProfile | null;
  online?: boolean;
  created_at?: string | null;
}

export interface ServerStatus {
  online: boolean;
  count: number;
  max: number;
  players: string[];
  tps?: number | null;
  uptime?: string | null;
  ram?: string | null;
  version?: string;
  name?: string;
  hosting_state?: string | null;
  cpu_percent?: number | null;
  memory_mb?: number | null;
  memory_limit_mb?: number | null;
  disk_mb?: number | null;
  disk_limit_mb?: number | null;
  panel_url?: string | null;
  address?: string | null;
  address_alias?: string | null;
  address_anycast?: string | null;
  motd?: string | null;
  latency_ms?: number | null;
  node?: string | null;
  location?: string | null;
  uptime_seconds?: number | null;
  source?: string | null;
}

export interface InventoryItem {
  slot: number;
  material: string;
  amount: number;
  name?: string | null;
  custom_name?: string | null;
  enchantments?: { id: string; level: number }[];
  durability?: number | null;
  max_durability?: number | null;
  custom_model_data?: number | null;
}

export interface TicketItem {
  id: number;
  text: string;
  status: string;
  category?: string;
  admin_comment?: string | null;
  created_at?: string | null;
  offender_nick?: string | null;
  attachments?: ReportAttachment[];
}

export interface ReportAttachment {
  id: number;
  kind: string;
  telegram_file_id?: string | null;
  caption?: string | null;
}

export interface LinkHistoryItem {
  id: number;
  telegram_id: number;
  nickname: string;
  uuid?: string | null;
  action: string;
  method: string;
  previous_nickname?: string | null;
  previous_telegram_id?: number | null;
  created_at?: string | null;
  note?: string | null;
}

export interface ServerAlert {
  type: string;
  message: string;
  player?: string;
}

export interface NewsItem {
  id: number;
  title: string;
  text: string;
  created_at?: string | null;
}

export interface BuildItem {
  id: number;
  name: string;
  platform: string;
  url: string;
  version: string;
  file_size: string;
  instruction: string;
}

declare global {
  interface Window {
    Telegram?: {
      WebApp: {
        initData: string;
        initDataUnsafe: Record<string, unknown>;
        ready: () => void;
        expand: () => void;
        close: () => void;
        colorScheme: "light" | "dark";
        themeParams: Record<string, string>;
        viewportHeight: number;
        headerColor: string;
        backgroundColor: string;
        setHeaderColor: (color: string) => void;
        setBackgroundColor: (color: string) => void;
        enableClosingConfirmation: () => void;
        onEvent?: (event: string, callback: () => void) => void;
        openLink?: (url: string) => void;
        HapticFeedback: {
          impactOccurred: (style: "light" | "medium" | "heavy" | "rigid" | "soft") => void;
          notificationOccurred: (type: "error" | "success" | "warning") => void;
          selectionChanged: () => void;
        };
        BackButton: {
          show: () => void;
          hide: () => void;
          onClick: (cb: () => void) => void;
          offClick: (cb: () => void) => void;
        };
        MainButton: {
          text: string;
          show: () => void;
          hide: () => void;
          setText: (text: string) => void;
          onClick: (cb: () => void) => void;
          offClick: (cb: () => void) => void;
          enable: () => void;
          disable: () => void;
          showProgress: (leaveActive?: boolean) => void;
          hideProgress: () => void;
        };
      };
    };
  }
}

export {};
