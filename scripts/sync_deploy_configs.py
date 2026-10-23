#!/usr/bin/env python3
"""Sync deploy configs from .env and print server install commands."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
PLUGIN_CONFIG = ROOT / "plugin" / "src" / "main" / "resources" / "config.yml"
DEPLOY_CONFIG = ROOT / "deploy" / "BydloBridge" / "config.yml"
DEPLOY_SERVER = ROOT / "deploy" / "config-server.yml"


def read_env() -> dict[str, str]:
    data: dict[str, str] = {}
    if not ENV_PATH.exists():
        return data
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def write_plugin_config(webapp_url: str, api_key: str) -> str:
    body = (
        f"http-port: 8765\n"
        f'api-key: "{api_key}"\n'
        f'backend-url: "{webapp_url.rstrip("/")}"\n'
        f'bind-address: "0.0.0.0"\n'
    )
    PLUGIN_CONFIG.write_text(body, encoding="utf-8")
    DEPLOY_CONFIG.write_text(body, encoding="utf-8")
    DEPLOY_SERVER.write_text(body, encoding="utf-8")
    return body


def main() -> None:
    env = read_env()
    webapp = env.get("WEBAPP_URL", "http://127.0.0.1:8080")
    api_key = env.get("PLUGIN_API_KEY", "")
    rcon_password = env.get("RCON_PASSWORD", "")
    jar_url = f"{webapp.rstrip('/')}/BydloBridge-1.0.0.jar"
    config_body = write_plugin_config(webapp, api_key)

    print("=== BydloBridge + RCON (консоль сервера) ===\n")
    print("cd plugins")
    print(f"curl -fsSL -o BydloBridge-1.0.0.jar {jar_url}")
    print("mkdir -p BydloBridge")
    print("cat > BydloBridge/config.yml << 'EOF'")
    print(config_body, end="")
    print("EOF")
    print()
    print("# RCON (server.properties):")
    print("enable-rcon=true")
    print("rcon.port=25575")
    if rcon_password:
        print(f"rcon.password={rcon_password}")
    else:
        print("rcon.password=SET_IN_ENV")
    print("broadcast-rcon-to-ops=false")
    print()
    print("restart")


if __name__ == "__main__":
    main()
