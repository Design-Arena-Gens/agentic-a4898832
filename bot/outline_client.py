from __future__ import annotations

import asyncio
import ssl
from dataclasses import dataclass

import aiohttp

from .config import load_config


def _fingerprint_from_hex(hex_value: str) -> bytes:
    cleaned = hex_value.replace(":", "").replace(" ", "").lower()
    return bytes.fromhex(cleaned)


@dataclass(slots=True)
class OutlineKey:
    key_id: str
    access_url: str
    port: int | None = None


class OutlineClient:
    def __init__(self) -> None:
        config = load_config().outline
        fingerprint = _fingerprint_from_hex(config.cert_sha256)
        ssl_context = ssl.create_default_context()
        self._connector = aiohttp.TCPConnector(ssl=aiohttp.Fingerprint(fingerprint))
        self._base_url = config.api_url.rstrip("/")
        self._timeout = aiohttp.ClientTimeout(total=config.timeout)
        self._session: aiohttp.ClientSession | None = None
        self._lock = asyncio.Lock()

    async def _get_session(self) -> aiohttp.ClientSession:
        async with self._lock:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession(
                    connector=self._connector,
                    timeout=self._timeout,
                    raise_for_status=True,
                )
        return self._session

    async def close(self) -> None:
        async with self._lock:
            if self._session and not self._session.closed:
                await self._session.close()

    async def create_key(self, label: str | None = None) -> OutlineKey:
        session = await self._get_session()
        payload = {"name": label} if label else {}
        async with session.post(f"{self._base_url}/access-keys", json=payload) as response:
            data = await response.json()
        return OutlineKey(
            key_id=data["id"],
            access_url=data["accessUrl"],
            port=data.get("port"),
        )


outline_client = OutlineClient()
