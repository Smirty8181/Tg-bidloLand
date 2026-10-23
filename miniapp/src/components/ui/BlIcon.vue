<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    :class="['bl-icon', colorClass]"
    aria-hidden="true"
    v-html="paths"
  />
</template>

<script setup lang="ts">
import { computed } from "vue";

export type IconName =
  | "home"
  | "players"
  | "profile"
  | "more"
  | "sword"
  | "skull"
  | "clock"
  | "map"
  | "chest"
  | "build"
  | "news"
  | "report"
  | "idea"
  | "whitelist"
  | "link"
  | "admin"
  | "server"
  | "online"
  | "offline"
  | "bolt"
  | "pickaxe"
  | "chevron"
  | "refresh"
  | "shield";

const props = withDefaults(
  defineProps<{ name: IconName; size?: number; tone?: "gold" | "red" | "blue" | "white" | "muted" }>(),
  { size: 20, tone: "white" }
);

const colorClass = computed(() => `bl-icon--${props.tone}`);

const ICONS: Record<IconName, string> = {
  home: `<rect x="3" y="11" width="7" height="7" fill="currentColor"/><rect x="14" y="8" width="7" height="10" fill="currentColor" opacity=".7"/><rect x="5" y="9" width="3" height="2" fill="#07080d"/><rect x="16" y="6" width="3" height="2" fill="#07080d"/>`,
  players: `<rect x="2" y="8" width="8" height="8" fill="currentColor"/><rect x="14" y="8" width="8" height="8" fill="currentColor" opacity=".75"/><rect x="4" y="5" width="4" height="3" fill="currentColor"/><rect x="16" y="5" width="4" height="3" fill="currentColor" opacity=".75"/>`,
  profile: `<rect x="6" y="4" width="12" height="6" fill="currentColor"/><rect x="4" y="11" width="16" height="9" fill="currentColor" opacity=".85"/><rect x="8" y="6" width="2" height="2" fill="#07080d"/><rect x="14" y="6" width="2" height="2" fill="#07080d"/>`,
  more: `<rect x="5" y="5" width="4" height="4" fill="currentColor"/><rect x="10" y="5" width="4" height="4" fill="currentColor"/><rect x="15" y="5" width="4" height="4" fill="currentColor"/><rect x="5" y="10" width="4" height="4" fill="currentColor" opacity=".7"/><rect x="10" y="10" width="4" height="4" fill="currentColor" opacity=".7"/><rect x="15" y="10" width="4" height="4" fill="currentColor" opacity=".7"/>`,
  sword: `<rect x="10" y="2" width="4" height="12" fill="currentColor"/><rect x="6" y="12" width="12" height="3" fill="currentColor" opacity=".8"/><rect x="9" y="15" width="6" height="5" fill="currentColor" opacity=".6"/><rect x="11" y="3" width="2" height="2" fill="#fff" opacity=".35"/>`,
  skull: `<rect x="7" y="6" width="10" height="9" fill="currentColor"/><rect x="8" y="9" width="2" height="2" fill="#07080d"/><rect x="14" y="9" width="2" height="2" fill="#07080d"/><rect x="10" y="13" width="4" height="1" fill="#07080d"/><rect x="9" y="15" width="2" height="3" fill="currentColor" opacity=".7"/><rect x="13" y="15" width="2" height="3" fill="currentColor" opacity=".7"/>`,
  clock: `<rect x="4" y="4" width="16" height="16" fill="currentColor" opacity=".2"/><rect x="6" y="6" width="12" height="12" fill="currentColor"/><rect x="11" y="8" width="2" height="6" fill="#07080d"/><rect x="11" y="12" width="5" height="2" fill="#07080d"/>`,
  map: `<rect x="4" y="5" width="16" height="14" fill="currentColor" opacity=".25"/><rect x="5" y="6" width="14" height="12" fill="currentColor"/><rect x="7" y="9" width="4" height="2" fill="#1E6BFF"/><rect x="12" y="11" width="5" height="2" fill="#E31B23"/><rect x="8" y="14" width="6" height="2" fill="#F5C518"/>`,
  chest: `<rect x="4" y="8" width="16" height="10" fill="currentColor"/><rect x="4" y="6" width="16" height="3" fill="currentColor" opacity=".8"/><rect x="10" y="10" width="4" height="4" fill="#07080d" opacity=".35"/><rect x="11" y="11" width="2" height="2" fill="#F5C518"/>`,
  build: `<rect x="5" y="7" width="14" height="11" fill="currentColor"/><rect x="5" y="5" width="14" height="3" fill="currentColor" opacity=".75"/><rect x="11" y="10" width="2" height="5" fill="#07080d" opacity=".35"/>`,
  news: `<rect x="4" y="6" width="12" height="12" fill="currentColor"/><rect x="16" y="8" width="4" height="8" fill="currentColor" opacity=".7"/><rect x="6" y="9" width="8" height="2" fill="#07080d" opacity=".3"/><rect x="6" y="13" width="6" height="2" fill="#07080d" opacity=".3"/>`,
  report: `<rect x="6" y="3" width="12" height="18" fill="currentColor"/><rect x="8" y="7" width="8" height="2" fill="#07080d" opacity=".25"/><rect x="8" y="11" width="6" height="2" fill="#07080d" opacity=".25"/><rect x="15" y="16" width="4" height="4" fill="#E31B23"/>`,
  idea: `<rect x="10" y="3" width="4" height="3" fill="currentColor"/><rect x="7" y="6" width="10" height="9" fill="currentColor" opacity=".9"/><rect x="9" y="15" width="6" height="2" fill="currentColor" opacity=".7"/><rect x="10" y="17" width="4" height="3" fill="currentColor" opacity=".5"/><rect x="11" y="8" width="2" height="4" fill="#F5C518"/>`,
  whitelist: `<rect x="4" y="5" width="16" height="14" fill="currentColor" opacity=".25"/><rect x="6" y="7" width="12" height="10" fill="currentColor"/><rect x="9" y="11" width="3" height="3" fill="#07080d" opacity=".2"/><rect x="12" y="12" width="5" height="2" fill="#07080d" opacity=".2"/>`,
  link: `<rect x="4" y="10" width="7" height="4" fill="currentColor"/><rect x="13" y="10" width="7" height="4" fill="currentColor" opacity=".75"/><rect x="9" y="11" width="6" height="2" fill="#F5C518"/>`,
  admin: `<rect x="5" y="5" width="14" height="14" fill="currentColor" opacity=".2"/><rect x="7" y="7" width="10" height="10" fill="currentColor"/><rect x="9" y="9" width="2" height="2" fill="#07080d"/><rect x="13" y="9" width="2" height="2" fill="#07080d"/><rect x="9" y="13" width="6" height="2" fill="#07080d"/>`,
  server: `<rect x="4" y="6" width="16" height="12" fill="currentColor"/><rect x="6" y="8" width="4" height="2" fill="#1E6BFF"/><rect x="11" y="8" width="4" height="2" fill="#1E6BFF"/><rect x="6" y="12" width="12" height="4" fill="#07080d" opacity=".25"/><rect x="8" y="4" width="2" height="2" fill="currentColor" opacity=".7"/><rect x="14" y="4" width="2" height="2" fill="currentColor" opacity=".7"/>`,
  online: `<rect x="6" y="6" width="12" height="12" fill="#3ecf6e"/><rect x="8" y="8" width="8" height="8" fill="#7dffb0" opacity=".55"/>`,
  offline: `<rect x="6" y="6" width="12" height="12" fill="#e31b23"/><rect x="8" y="8" width="8" height="8" fill="#ff6b6b" opacity=".45"/>`,
  bolt: `<rect x="11" y="2" width="4" height="6" fill="currentColor"/><rect x="7" y="8" width="10" height="4" fill="currentColor"/><rect x="9" y="12" width="6" height="8" fill="currentColor" opacity=".8"/>`,
  pickaxe: `<rect x="4" y="4" width="4" height="4" fill="currentColor"/><rect x="8" y="8" width="4" height="4" fill="currentColor"/><rect x="12" y="12" width="4" height="4" fill="currentColor"/><rect x="16" y="16" width="4" height="4" fill="currentColor" opacity=".75"/>`,
  chevron: `<rect x="8" y="6" width="3" height="12" fill="currentColor" transform="rotate(-45 9.5 12)"/><rect x="13" y="6" width="3" height="12" fill="currentColor" transform="rotate(45 14.5 12)"/>`,
  refresh: `<rect x="10" y="3" width="8" height="3" fill="currentColor"/><rect x="17" y="5" width="3" height="8" fill="currentColor"/><rect x="6" y="18" width="8" height="3" fill="currentColor" opacity=".8"/><rect x="4" y="11" width="3" height="8" fill="currentColor" opacity=".8"/>`,
  shield: `<rect x="6" y="4" width="12" height="4" fill="currentColor"/><rect x="5" y="8" width="14" height="8" fill="currentColor" opacity=".85"/><rect x="8" y="16" width="8" height="4" fill="currentColor" opacity=".65"/>`,
};

const paths = computed(() => ICONS[props.name] || "");
</script>

<style scoped>
.bl-icon {
  display: block;
  flex-shrink: 0;
}
.bl-icon--gold { color: #f5c518; }
.bl-icon--red { color: #e31b23; }
.bl-icon--blue { color: #1e6bff; }
.bl-icon--white { color: #f4f7ff; }
.bl-icon--muted { color: #8b93a7; }
</style>
