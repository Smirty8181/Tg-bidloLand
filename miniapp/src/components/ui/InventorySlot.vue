<template>
  <button
    class="relative flex h-10 w-10 items-center justify-center border-2 border-[#0a0a0a] text-[10px] font-bold uppercase"
    :class="slotClass"
    :style="{ background: itemColor }"
    @click="$emit('click')"
  >
    <span v-if="item" class="text-white drop-shadow">{{ shortLabel }}</span>
    <span v-if="item && item.amount > 1" class="absolute bottom-0 right-0 bg-black/70 px-0.5 text-[9px] leading-none text-white">
      {{ item.amount }}
    </span>
  </button>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { InventoryItem } from "../../types";

const props = defineProps<{ item?: InventoryItem | null }>();
defineEmits<{ click: [] }>();

const MATERIAL_COLORS: Record<string, string> = {
  DIAMOND: "#4ee0c7",
  DIAMOND_SWORD: "#4ee0c7",
  DIAMOND_PICKAXE: "#4ee0c7",
  NETHERITE: "#5a4a62",
  GOLDEN: "#f5c518",
  IRON: "#c8c8c8",
  STONE: "#8a8a8a",
  APPLE: "#e31b23",
  BOW: "#a88408",
  ARROW: "#d4d4d4",
};

const shortLabel = computed(() => {
  if (!props.item) return "";
  const name = props.item.custom_name || props.item.name || props.item.material;
  return name.slice(0, 2);
});

const itemColor = computed(() => {
  if (!props.item) return "#2b2b2b";
  const mat = props.item.material;
  for (const [key, color] of Object.entries(MATERIAL_COLORS)) {
    if (mat.includes(key)) return color;
  }
  return "#3d4a5c";
});

const slotClass = computed(() => (props.item ? "shadow-[inset_0_-2px_0_rgba(0,0,0,.4)]" : "opacity-60"));
</script>
