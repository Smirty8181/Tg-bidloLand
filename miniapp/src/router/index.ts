import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import PlayersView from "../views/PlayersView.vue";
import ProfileView from "../views/ProfileView.vue";
import InventoryView from "../views/InventoryView.vue";
import MapView from "../views/MapView.vue";
import BuildView from "../views/BuildView.vue";
import WhitelistView from "../views/WhitelistView.vue";
import LinkView from "../views/LinkView.vue";
import TicketsView from "../views/TicketsView.vue";
import NewsView from "../views/NewsView.vue";
import MoreView from "../views/MoreView.vue";
import AdminHomeView from "../views/admin/AdminHomeView.vue";
import AdminInboxView from "../views/admin/AdminInboxView.vue";
import AdminPlayersView from "../views/admin/AdminPlayersView.vue";
import AdminServerView from "../views/admin/AdminServerView.vue";
import AdminNewsView from "../views/admin/AdminNewsView.vue";
import AdminBuildsView from "../views/admin/AdminBuildsView.vue";
import AdminStaffView from "../views/admin/AdminStaffView.vue";
import AdminLinksView from "../views/admin/AdminLinksView.vue";
import PlayerView from "../views/PlayerView.vue";
import AdminPlayerDetailView from "../views/admin/AdminPlayerDetailView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: HomeView },
    { path: "/server", component: PlayersView },
    { path: "/player/:name", component: PlayerView },
    { path: "/profile", component: ProfileView },
    { path: "/inventory", component: InventoryView },
    { path: "/map", component: MapView },
    { path: "/build", component: BuildView },
    { path: "/whitelist", component: WhitelistView },
    { path: "/link", component: LinkView },
    { path: "/reports", component: TicketsView, props: { mode: "reports" } },
    { path: "/suggestions", component: TicketsView, props: { mode: "suggestions" } },
    { path: "/ideas", component: TicketsView, props: { mode: "ideas" } },
    { path: "/news", component: NewsView },
    { path: "/more", component: MoreView },
    { path: "/admin", component: AdminHomeView },
    { path: "/admin/reports", redirect: { path: "/admin/inbox", query: { kind: "report" } } },
    { path: "/admin/inbox", component: AdminInboxView },
    { path: "/admin/players", component: AdminPlayersView },
    { path: "/admin/players/:nick", component: AdminPlayerDetailView },
    { path: "/admin/links", component: AdminLinksView },
    { path: "/admin/server", component: AdminServerView },
    { path: "/admin/news", component: AdminNewsView },
    { path: "/admin/builds", component: AdminBuildsView },
    { path: "/admin/staff", component: AdminStaffView },
  ],
  scrollBehavior() {
    return { top: 0 };
  },
});

export default router;
