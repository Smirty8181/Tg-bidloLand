<template>
  <div class="loader flex flex-col items-center justify-center gap-5 py-16">
    <div class="loader__orb" aria-hidden="true">
      <img src="/logo.jpg" alt="" class="loader__logo" />
    </div>
    <div class="loader__bars" aria-hidden="true">
      <span v-for="i in 4" :key="i" class="loader__bar" :style="{ animationDelay: `${i * 100}ms` }" />
    </div>
    <p class="label-caps">Загрузка</p>
  </div>
</template>

<style scoped>
.loader__orb {
  position: relative;
  width: 56px;
  height: 56px;
  animation: float 3s ease-in-out infinite;
}

.loader__logo {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  object-fit: cover;
  border: 2px solid rgba(245, 197, 24, 0.35);
  box-shadow: 0 0 24px rgba(245, 197, 24, 0.2);
}

.loader__bars {
  display: flex;
  gap: 6px;
}

.loader__bar {
  width: 6px;
  height: 22px;
  border-radius: 999px;
  background: linear-gradient(180deg, var(--gold), rgba(245, 197, 24, 0.2));
  animation: bar-pulse 0.9s ease-in-out infinite;
}

@keyframes bar-pulse {
  0%,
  100% {
    transform: scaleY(0.55);
    opacity: 0.35;
  }
  50% {
    transform: scaleY(1);
    opacity: 1;
  }
}
</style>
