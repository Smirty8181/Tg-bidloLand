<template>
  <img :src="src" :alt="alt" class="h-12 w-12 rounded-2xl object-cover shadow-card ring-2 ring-gold/40" />
</template>
<script setup lang="ts">
withDefaults(defineProps<{ src?: string; alt?: string }>(), { src: "/logo.jpg", alt: "БыдлоЛенд" });
</script>
