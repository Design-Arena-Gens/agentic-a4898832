from __future__ import annotations

import asyncio
import time
from collections import defaultdict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from .config import load_config
from .database import async_session_factory


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        super().__init__()
        config = load_config()
        self.limit = config.rate_limit_per_minute
        self.window = 60
        self._storage: dict[int, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def __call__(
        self,
        handler,
        event: TelegramObject,
        data: dict,
    ):
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
            if user_id:
                async with self._lock:
                    timestamps = self._storage[user_id]
                    now = time.monotonic()
                    timestamps[:] = [t for t in timestamps if now - t <= self.window]
                    if len(timestamps) >= self.limit:
                        await event.answer("🛑 Притормози, босс. Дай секунду отдышаться.")
                        return
                    timestamps.append(now)
        return await handler(event, data)


class DatabaseSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        async with async_session_factory() as session:
            try:
                data["session"] = session
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
