import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import { useTelegram } from "./composables/useTelegram";
import { useTheme } from "./composables/useTheme";
import "./styles/main.css";

const { ready } = useTelegram();
ready();
useTheme();

createApp(App).use(createPinia()).use(router).mount("#app");
