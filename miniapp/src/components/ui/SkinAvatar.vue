<template>
  <img
    :src="src"
    :alt="nickname || 'skin'"
    class="skin-avatar"
    :class="[`skin-avatar--${size}`]"
    loading="lazy"
    @error="onError"
  />
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

const props = withDefaults(
  defineProps<{ nickname?: string | null; uuid?: string | null; size?: "sm" | "md" | "lg" | "xl" }>(),
  { size: "md" },
);

const failed = ref(false);

const src = computed(() => {
  if (failed.value || (!props.nickname && !props.uuid)) {
    return "/logo.jpg";
  }
  const id = props.uuid || props.nickname;
  const px = props.size === "xl" ? 128 : props.size === "lg" ? 96 : props.size === "sm" ? 32 : 64;
  return `https://mc-heads.net/avatar/${encodeURIComponent(id!)}/${px}`;
});

watch(
  () => [props.nickname, props.uuid],
  () => {
    failed.value = false;
  },
);

function onError() {
  failed.value = true;
}
</script>

<style scoped>
.skin-avatar {
  border-radius: 22%;
  object-fit: cover;
  background: #0d0e13;
  border: 2px solid rgba(245, 197, 24, 0.25);
  box-shadow: 0 0 20px rgba(245, 197, 24, 0.08);
}

.skin-avatar--sm {
  width: 32px;
  height: 32px;
}

.skin-avatar--md {
  width: 56px;
  height: 56px;
}

.skin-avatar--lg {
  width: 80px;
  height: 80px;
}

.skin-avatar--xl {
  width: 96px;
  height: 96px;
  border-radius: 20px;
}
</style>
