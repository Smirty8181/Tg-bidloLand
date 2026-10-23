<template>
  <RouterView v-slot="{ Component, route }">
    <Transition name="route" mode="out-in">
      <component :is="Component" :key="route.path" />
    </Transition>
  </RouterView>
</template>

<style>
.route-enter-active,
.route-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.route-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.route-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
