<template>
  <section v-if="visible" class="onboarding mc-panel mc-panel--gold">
    <div class="onboarding__head">
      <div class="section-head !mb-0">
        <BlIcon name="link" :size="14" tone="gold" />
        <p class="label-caps !mb-0">Как привязать Minecraft</p>
      </div>
      <button v-if="dismissible" type="button" class="onboarding__close pressable" aria-label="Скрыть" @click="dismiss">
        ✕
      </button>
    </div>

    <div class="onboarding__steps">
      <div
        v-for="(step, index) in steps"
        :key="step.title"
        class="onboarding-step"
        :class="index <= activeStep ? 'onboarding-step--done' : ''"
      >
        <span class="onboarding-step__num">{{ index + 1 }}</span>
        <div>
          <p class="onboarding-step__title">{{ step.title }}</p>
          <p class="onboarding-step__text">{{ step.text }}</p>
        </div>
      </div>
    </div>

    <RouterLink v-if="!hideCta" to="/link" class="mc-btn mc-btn--gold onboarding__cta pressable w-full" @click="onStart">
      {{ ctaLabel }}
    </RouterLink>
    <p v-if="dismissible" class="onboarding__hint">Можно скрыть — баннер вернётся, пока аккаунт не привязан.</p>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { RouterLink } from "vue-router";
import BlIcon from "./BlIcon.vue";
import { useTelegram } from "../../composables/useTelegram";

const props = withDefaults(
  defineProps<{
    linked?: boolean;
    dismissible?: boolean;
    compact?: boolean;
    hideCta?: boolean;
  }>(),
  { linked: false, dismissible: true, compact: false, hideCta: false },
);

const STORAGE_KEY = "bydloland.onboarding.v1.dismissed";
const dismissed = ref(false);
const { haptic } = useTelegram();

const steps = [
  { title: "Открой раздел «Привязка»", text: "Mini App должен быть открыт с нужного Telegram-аккаунта." },
  { title: "Введи свой Minecraft-ник", text: "Например Smirty_228 — и нажми «Привязать»." },
  { title: "Готово!", text: "Придёт сообщение в Telegram. Откроются инвентарь, whitelist и профиль." },
];

const activeStep = computed(() => (props.linked ? 2 : 0));
const ctaLabel = computed(() => (props.linked ? "Привязка выполнена" : "Начать привязку"));

const visible = computed(() => !props.linked && (!props.dismissible || !dismissed.value));

function readDismissed() {
  try {
    dismissed.value = localStorage.getItem(STORAGE_KEY) === "1";
  } catch {
    dismissed.value = false;
  }
}

function dismiss() {
  dismissed.value = true;
  try {
    localStorage.setItem(STORAGE_KEY, "1");
  } catch {
    /* ignore */
  }
  haptic("light");
}

function onStart() {
  haptic("light");
}

watch(
  () => props.linked,
  (linked) => {
    if (linked) {
      try {
        localStorage.removeItem(STORAGE_KEY);
      } catch {
        /* ignore */
      }
    }
  },
);

readDismissed();
</script>

<style scoped>
.onboarding {
  padding: 16px;
  border-radius: var(--radius-lg);
}

.onboarding__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.onboarding__close {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.04);
  color: var(--muted);
  font-size: 12px;
  cursor: pointer;
}

.onboarding__steps {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 14px;
}

.onboarding-step {
  display: flex;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--line);
  background: rgba(0, 0, 0, 0.15);
  opacity: 0.55;
  transition: opacity 0.2s ease, border-color 0.2s ease;
}

.onboarding-step--done {
  opacity: 1;
  border-color: rgba(232, 176, 32, 0.22);
}

.onboarding-step__num {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 8px;
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 800;
  color: var(--gold-soft);
  background: rgba(232, 176, 32, 0.12);
  border: 1px solid rgba(232, 176, 32, 0.25);
}

.onboarding-step__title {
  margin: 0;
  font-size: 13px;
  font-weight: 800;
}

.onboarding-step__text {
  margin: 4px 0 0;
  font-size: 11px;
  line-height: 1.45;
  color: var(--muted);
}

.onboarding__cta {
  margin-top: 4px;
}

.onboarding__hint {
  margin: 10px 0 0;
  text-align: center;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.35);
}
</style>
