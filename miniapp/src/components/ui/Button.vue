<template>
  <button
    class="pressable inline-flex min-h-[46px] w-full items-center justify-center gap-2 rounded-xl border px-4 text-sm font-extrabold tracking-wide transition disabled:opacity-45"
    :class="classes"
    :disabled="disabled"
    @click="$emit('click')"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{ variant?: "gold" | "red" | "blue" | "ghost"; disabled?: boolean; size?: "md" | "sm" }>(),
  { variant: "gold", disabled: false, size: "md" },
);
defineEmits<{ click: [] }>();

const classes = computed(() => {
  const size = props.size === "sm" ? "min-h-[40px] text-xs" : "";
  if (props.variant === "red")
    return `${size} border-crimson/50 bg-gradient-to-b from-crimson to-[#c92a38] text-white shadow-[0_6px_20px_rgba(255,71,87,0.25)]`;
  if (props.variant === "blue")
    return `${size} border-royal/50 bg-gradient-to-b from-royal to-[#2563eb] text-white shadow-[0_6px_20px_rgba(77,141,255,0.25)]`;
  if (props.variant === "ghost")
    return `${size} border-[var(--line-strong)] bg-white/[0.03] text-white`;
  return `${size} border-gold/40 bg-gradient-to-b from-gold/25 to-gold/10 text-gold-soft shadow-[0_6px_24px_rgba(245,197,24,0.18)]`;
});
</script>
