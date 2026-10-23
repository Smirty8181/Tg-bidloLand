from __future__ import annotations

import asyncio
import logging
import struct
from typing import Optional

from config.settings import settings

logger = logging.getLogger(__name__)


class MinecraftUnavailable(Exception):
    """RCON or plugin is unreachable. Never include secrets in the message."""


class RconClient:
    SERVERDATA_AUTH = 3
    SERVERDATA_AUTH_RESPONSE = 2
    SERVERDATA_EXECCOMMAND = 2
    SERVERDATA_RESPONSE_VALUE = 0

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        password: Optional[str] = None,
        timeout: float = 6.0,
    ) -> None:
        self.host = host or settings.rcon_host
        self.port = port or settings.rcon_port
        self.password = password if password is not None else settings.rcon_password
        self.timeout = timeout
        self._req_id = 0

    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    @staticmethod
    def _encode(req_id: int, req_type: int, payload: str) -> bytes:
        body = struct.pack("<ii", req_id, req_type) + payload.encode("utf-8") + b"\x00\x00"
        return struct.pack("<i", len(body)) + body

    async def _read_packet(self, reader: asyncio.StreamReader) -> tuple[int, int, str]:
        header = await asyncio.wait_for(reader.readexactly(4), timeout=self.timeout)
        (length,) = struct.unpack("<i", header)
        if length < 10 or length > 4110:
            raise MinecraftUnavailable("Некорректный ответ RCON")
        data = await asyncio.wait_for(reader.readexactly(length), timeout=self.timeout)
        req_id, req_type = struct.unpack("<ii", data[:8])
        payload = data[8:-2].decode("utf-8", errors="replace")
        return req_id, req_type, payload

    async def execute(self, command: str) -> str:
        if not self.password:
            raise MinecraftUnavailable("RCON не настроен")
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), timeout=self.timeout
            )
        except Exception as exc:
            logger.error("RCON connection failed: %s", type(exc).__name__)
            raise MinecraftUnavailable("Не удалось связаться с Minecraft-сервером") from None

        try:
            auth_id = self._next_id()
            writer.write(self._encode(auth_id, self.SERVERDATA_AUTH, self.password))
            await writer.drain()
            try:
                resp_id, _, _ = await self._read_packet(reader)
            except Exception:
                logger.error("RCON auth failed")
                raise MinecraftUnavailable("Не удалось связаться с Minecraft-сервером") from None
            if resp_id == -1 or resp_id != auth_id:
                logger.error("RCON authentication rejected")
                raise MinecraftUnavailable("Не удалось связаться с Minecraft-сервером")

            cmd_id = self._next_id()
            writer.write(self._encode(cmd_id, self.SERVERDATA_EXECCOMMAND, command.lstrip("/")))
            await writer.drain()
            chunks: list[str] = []
            while True:
                _, _, payload = await self._read_packet(reader)
                chunks.append(payload)
                if reader.at_eof():
                    break
                # Paper usually replies with a single packet.
                if len(payload) < 4096:
                    break
            return "".join(chunks).strip()
        except MinecraftUnavailable:
            raise
        except Exception as exc:
            logger.error("RCON command failed: %s", type(exc).__name__)
            raise MinecraftUnavailable("Не удалось связаться с Minecraft-сервером") from None
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
