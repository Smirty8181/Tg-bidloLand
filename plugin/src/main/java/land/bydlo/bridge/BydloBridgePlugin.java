package land.bydlo.bridge;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import org.bukkit.Bukkit;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.OfflinePlayer;
import org.bukkit.Statistic;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.enchantments.Enchantment;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.player.AsyncPlayerChatEvent;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.Damageable;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.plugin.java.JavaPlugin;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

public final class BydloBridgePlugin extends JavaPlugin implements Listener {
    private final Gson gson = new Gson();
    private final HttpClient http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();
    private final Map<UUID, Long> mutedUntil = new ConcurrentHashMap<>();
    private HttpServer server;
    private long startedAt;

    @Override
    public void onEnable() {
        saveDefaultConfig();
        startedAt = System.currentTimeMillis();
        getServer().getPluginManager().registerEvents(this, this);
        try {
            startHttp();
            getLogger().info("BydloBridge HTTP started on " + getConfig().getInt("http-port"));
        } catch (IOException ex) {
            getLogger().severe("Failed to start HTTP API");
            getLogger().severe(ex.getClass().getSimpleName());
        }
        Bukkit.getScheduler().runTaskLater(this, this::pushStatusToBackend, 40L);
        Bukkit.getScheduler().runTaskTimer(this, this::pushStatusToBackend, 200L, 600L);
    }

    @Override
    public void onDisable() {
        if (server != null) {
            server.stop(0);
        }
    }

    private void startHttp() throws IOException {
        String bind = getConfig().getString("bind-address", "127.0.0.1");
        int port = getConfig().getInt("http-port", 8765);
        server = HttpServer.create(new InetSocketAddress(bind, port), 0);
        server.createContext("/server/status", this::handleStatus);
        server.createContext("/server/restart", this::handleRestart);
        server.createContext("/server/announce", this::handleAnnounce);
        server.createContext("/moderation", this::handleModeration);
        server.createContext("/whitelist/add", this::handleWhitelist);
        server.createContext("/player/", this::handlePlayer);
        server.setExecutor(null);
        server.start();
    }

    private boolean authorized(HttpExchange exchange) {
        String expected = getConfig().getString("api-key", "");
        String given = exchange.getRequestHeaders().getFirst("X-API-Key");
        return expected != null && !expected.isBlank() && expected.equals(given);
    }

    private void handleStatus(HttpExchange exchange) throws IOException {
        if (!guard(exchange, "GET")) return;
        Bukkit.getScheduler().runTask(this, () -> respond(exchange, 200, buildStatusJson()));
    }

    private JsonObject buildStatusJson() {
        JsonObject json = new JsonObject();
        json.addProperty("ok", true);
        json.addProperty("online", true);
        json.addProperty("version", Bukkit.getMinecraftVersion());
        json.addProperty("max", Bukkit.getMaxPlayers());
        json.addProperty("count", Bukkit.getOnlinePlayers().size());
        double tps = 20.0;
        try {
            tps = Bukkit.getTPS()[0];
        } catch (Throwable ignored) {
        }
        json.addProperty("tps", Math.round(tps * 10.0) / 10.0);
        Runtime rt = Runtime.getRuntime();
        long used = (rt.totalMemory() - rt.freeMemory()) / (1024 * 1024);
        long max = rt.maxMemory() / (1024 * 1024);
        json.addProperty("ram", used + " / " + max + " MB");
        long uptimeSeconds = (System.currentTimeMillis() - startedAt) / 1000;
        json.addProperty("uptime_seconds", uptimeSeconds);
        json.addProperty("uptime", uptimeSeconds + " сек");
        JsonArray players = new JsonArray();
        for (Player player : Bukkit.getOnlinePlayers()) {
            JsonObject p = new JsonObject();
            p.addProperty("name", player.getName());
            p.addProperty("uuid", player.getUniqueId().toString());
            players.add(p);
        }
        json.add("players", players);
        return json;
    }

    private void pushStatusToBackend() {
        String backend = getConfig().getString("backend-url", "");
        String key = getConfig().getString("api-key", "");
        if (backend == null || backend.isBlank()) {
            return;
        }
        JsonObject payload = buildStatusJson();
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(backend.replaceAll("/$", "") + "/api/internal/server-sync"))
                .header("Content-Type", "application/json")
                .header("X-API-Key", key)
                .POST(HttpRequest.BodyPublishers.ofString(payload.toString(), StandardCharsets.UTF_8))
                .timeout(Duration.ofSeconds(8))
                .build();
        http.sendAsync(request, HttpResponse.BodyHandlers.ofString()).thenAccept(response -> {
            if (response.statusCode() >= 200 && response.statusCode() < 300) {
                getLogger().fine("BydloBridge status pushed to backend");
            } else {
                getLogger().warning("BydloBridge status push failed: HTTP " + response.statusCode());
            }
        }).exceptionally(ex -> {
            getLogger().warning("BydloBridge status push failed: " + ex.getClass().getSimpleName());
            return null;
        });
    }

    private void handleRestart(HttpExchange exchange) throws IOException {
        if (!guard(exchange, "POST")) return;
        Bukkit.getScheduler().runTask(this, () -> {
            Bukkit.dispatchCommand(Bukkit.getConsoleSender(), "restart");
            respond(exchange, 200, ok());
        });
    }

    private void handleAnnounce(HttpExchange exchange) throws IOException {
        if (!guard(exchange, "POST")) return;
        JsonObject body = readJson(exchange);
        String message = body.has("message") ? body.get("message").getAsString() : "";
        Bukkit.getScheduler().runTask(this, () -> {
            Bukkit.broadcastMessage("§6[БыдлоЛенд] §f" + message);
            respond(exchange, 200, ok());
        });
    }

    private void handleWhitelist(HttpExchange exchange) throws IOException {
        if (!guard(exchange, "POST")) return;
        JsonObject body = readJson(exchange);
        String player = body.get("player").getAsString();
        Bukkit.getScheduler().runTask(this, () -> {
            boolean already = Bukkit.getWhitelistedPlayers().stream().anyMatch(p -> p.getName() != null && p.getName().equalsIgnoreCase(player));
            Bukkit.dispatchCommand(Bukkit.getConsoleSender(), "whitelist add " + player);
            JsonObject json = ok();
            json.addProperty("already", already);
            respond(exchange, 200, json);
        });
    }

    private void handleModeration(HttpExchange exchange) throws IOException {
        if (!guard(exchange, "POST")) return;
        JsonObject body = readJson(exchange);
        String action = body.get("action").getAsString();
        String player = body.get("player").getAsString();
        String reason = body.has("reason") ? body.get("reason").getAsString() : "punished";
        Integer duration = body.has("durationSeconds") && !body.get("durationSeconds").isJsonNull()
                ? body.get("durationSeconds").getAsInt() : null;
        Bukkit.getScheduler().runTask(this, () -> {
            Player online = Bukkit.getPlayerExact(player);
            switch (action) {
                case "kick" -> {
                    if (online != null) online.kick(net.kyori.adventure.text.Component.text(reason));
                }
                case "ban" -> Bukkit.dispatchCommand(Bukkit.getConsoleSender(), "ban " + player + " " + reason);
                case "mute" -> {
                    OfflinePlayer off = Bukkit.getOfflinePlayer(player);
                    long until = duration == null ? Long.MAX_VALUE : System.currentTimeMillis() + duration * 1000L;
                    mutedUntil.put(off.getUniqueId(), until);
                    if (online != null) online.sendMessage("§cВы замучены: " + reason);
                }
                case "warning", "warn" -> {
                    if (online != null) online.sendMessage("§eПредупреждение: " + reason);
                    Bukkit.broadcastMessage("§e[Warn] " + player + ": " + reason);
                }
                default -> {
                }
            }
            respond(exchange, 200, ok());
        });
    }

    private void handlePlayer(HttpExchange exchange) throws IOException {
        if (!guard(exchange, "GET")) return;
        String path = exchange.getRequestURI().getPath();
        String[] parts = path.split("/");
        if (parts.length < 4) {
            respond(exchange, 404, error("not_found"));
            return;
        }
        String lookup = parts[2];
        String kind = parts[3];
        Bukkit.getScheduler().runTask(this, () -> {
            Player player = resolve(lookup);
            if (player == null) {
                JsonObject json = error("not_found");
                json.addProperty("status", 404);
                json.addProperty("online", false);
                respond(exchange, 200, json);
                return;
            }
            JsonObject json = switch (kind) {
                case "inventory" -> inventory(player);
                case "stats" -> stats(player);
                default -> status(player);
            };
            respond(exchange, 200, json);
        });
    }

    private Player resolve(String lookup) {
        Player byName = Bukkit.getPlayerExact(lookup);
        if (byName != null) return byName;
        try {
            return Bukkit.getPlayer(UUID.fromString(lookup));
        } catch (IllegalArgumentException ignored) {
            return null;
        }
    }

    private JsonObject inventory(Player player) {
        JsonObject json = new JsonObject();
        json.addProperty("ok", true);
        json.addProperty("online", true);
        json.addProperty("player", player.getName());
        json.addProperty("uuid", player.getUniqueId().toString());
        JsonArray items = new JsonArray();
        ItemStack[] contents = player.getInventory().getContents();
        for (int i = 0; i < contents.length; i++) {
            ItemStack stack = contents[i];
            if (stack == null || stack.getType() == Material.AIR) continue;
            items.add(serialize(i, stack));
        }
        json.add("inventory", items);
        JsonObject armor = new JsonObject();
        armor.add("helmet", serializeItem(player.getInventory().getHelmet()));
        armor.add("chestplate", serializeItem(player.getInventory().getChestplate()));
        armor.add("leggings", serializeItem(player.getInventory().getLeggings()));
        armor.add("boots", serializeItem(player.getInventory().getBoots()));
        json.add("armor", armor);
        json.add("offhand", serializeItem(player.getInventory().getItemInOffHand()));
        syncBackend(json);
        return json;
    }

    private JsonObject serialize(int slot, ItemStack stack) {
        JsonObject item = serializeItem(stack).getAsJsonObject();
        item.addProperty("slot", slot);
        return item;
    }

    private com.google.gson.JsonElement serializeItem(ItemStack stack) {
        if (stack == null || stack.getType() == Material.AIR) {
            return com.google.gson.JsonNull.INSTANCE;
        }
        JsonObject item = new JsonObject();
        item.addProperty("material", stack.getType().name());
        item.addProperty("amount", stack.getAmount());
        ItemMeta meta = stack.getItemMeta();
        String pretty = stack.getType().name().toLowerCase(Locale.ROOT).replace('_', ' ');
        item.addProperty("name", pretty);
        if (meta != null) {
            if (meta.hasDisplayName()) {
                item.addProperty("custom_name", net.kyori.adventure.text.serializer.plain.PlainTextComponentSerializer.plainText().serialize(meta.displayName()));
            }
            if (meta.hasCustomModelData()) {
                item.addProperty("custom_model_data", meta.getCustomModelData());
            }
            if (meta instanceof Damageable damageable && stack.getType().getMaxDurability() > 0) {
                int max = stack.getType().getMaxDurability();
                item.addProperty("max_durability", max);
                item.addProperty("durability", max - damageable.getDamage());
            }
            JsonArray enchants = new JsonArray();
            for (Map.Entry<Enchantment, Integer> entry : meta.getEnchants().entrySet()) {
                JsonObject ench = new JsonObject();
                NamespacedKey key = entry.getKey().getKey();
                ench.addProperty("id", key.getKey());
                ench.addProperty("level", entry.getValue());
                enchants.add(ench);
            }
            item.add("enchantments", enchants);
        }
        return item;
    }

    private JsonObject stats(Player player) {
        JsonObject json = new JsonObject();
        json.addProperty("ok", true);
        json.addProperty("player", player.getName());
        json.addProperty("uuid", player.getUniqueId().toString());
        json.addProperty("kills", player.getStatistic(Statistic.PLAYER_KILLS));
        json.addProperty("deaths", player.getStatistic(Statistic.DEATHS));
        json.addProperty("playtime_seconds", player.getStatistic(Statistic.PLAY_ONE_MINUTE) / 20);
        json.addProperty("online", true);
        return json;
    }

    private JsonObject status(Player player) {
        JsonObject json = stats(player);
        json.addProperty("world", player.getWorld().getName());
        json.addProperty("x", player.getLocation().getX());
        json.addProperty("y", player.getLocation().getY());
        json.addProperty("z", player.getLocation().getZ());
        return json;
    }

    private void syncBackend(JsonObject inventory) {
        String backend = getConfig().getString("backend-url", "");
        String key = getConfig().getString("api-key", "");
        if (backend == null || backend.isBlank()) return;
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(backend.replaceAll("/$", "") + "/api/internal/player-sync"))
                .header("Content-Type", "application/json")
                .header("X-API-Key", key)
                .POST(HttpRequest.BodyPublishers.ofString(inventory.toString(), StandardCharsets.UTF_8))
                .timeout(Duration.ofSeconds(5))
                .build();
        http.sendAsync(request, HttpResponse.BodyHandlers.discarding());
    }

    @EventHandler
    public void onChat(AsyncPlayerChatEvent event) {
        Long until = mutedUntil.get(event.getPlayer().getUniqueId());
        if (until != null && until > System.currentTimeMillis()) {
            event.setCancelled(true);
            event.getPlayer().sendMessage("§cВы замучены.");
        }
    }

    @EventHandler
    public void onQuit(PlayerQuitEvent event) {
        Bukkit.getScheduler().runTask(this, () -> syncBackend(inventory(event.getPlayer())));
    }

    @EventHandler
    public void onJoin(PlayerJoinEvent event) {
        Bukkit.getScheduler().runTask(this, () -> syncBackend(inventory(event.getPlayer())));
    }

    @Override
    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (!command.getName().equalsIgnoreCase("link")) return false;
        if (!(sender instanceof Player player)) {
            sender.sendMessage("Only players");
            return true;
        }
        if (args.length != 1) {
            player.sendMessage("§eИспользование: /link <код>");
            return true;
        }
        JsonObject body = new JsonObject();
        body.addProperty("code", args[0]);
        body.addProperty("uuid", player.getUniqueId().toString());
        body.addProperty("nickname", player.getName());
        String backend = getConfig().getString("backend-url", "http://127.0.0.1:8080");
        String key = getConfig().getString("api-key", "");
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(backend.replaceAll("/$", "") + "/api/internal/link"))
                .header("Content-Type", "application/json")
                .header("X-API-Key", key)
                .POST(HttpRequest.BodyPublishers.ofString(body.toString(), StandardCharsets.UTF_8))
                .timeout(Duration.ofSeconds(8))
                .build();
        http.sendAsync(request, HttpResponse.BodyHandlers.ofString()).thenAccept(response -> {
            if (response.statusCode() >= 200 && response.statusCode() < 300) {
                player.sendMessage("§aАккаунт успешно привязан к Telegram.");
            } else {
                player.sendMessage("§cНе удалось привязать аккаунт. Проверьте код.");
            }
        });
        player.sendMessage("§7Проверяем код...");
        return true;
    }

    private boolean guard(HttpExchange exchange, String method) throws IOException {
        if (!authorized(exchange)) {
            respond(exchange, 401, error("unauthorized"));
            return false;
        }
        if (!exchange.getRequestMethod().equalsIgnoreCase(method)) {
            respond(exchange, 405, error("method"));
            return false;
        }
        return true;
    }

    private JsonObject readJson(HttpExchange exchange) throws IOException {
        try (InputStream in = exchange.getRequestBody()) {
            String raw = new String(in.readAllBytes(), StandardCharsets.UTF_8);
            if (raw.isBlank()) return new JsonObject();
            return gson.fromJson(raw, JsonObject.class);
        }
    }

    private JsonObject ok() {
        JsonObject json = new JsonObject();
        json.addProperty("ok", true);
        return json;
    }

    private JsonObject error(String code) {
        JsonObject json = new JsonObject();
        json.addProperty("ok", false);
        json.addProperty("error", code);
        return json;
    }

    private void respond(HttpExchange exchange, int status, JsonObject body) {
        byte[] bytes = body.toString().getBytes(StandardCharsets.UTF_8);
        try {
            exchange.getResponseHeaders().add("Content-Type", "application/json; charset=utf-8");
            exchange.sendResponseHeaders(status, bytes.length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(bytes);
            }
        } catch (IOException ignored) {
        }
    }
}
