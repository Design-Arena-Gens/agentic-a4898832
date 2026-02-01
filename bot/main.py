import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from .config import load_config
from .database import init_db
from .handlers import admin, common, payments
from .middlewares import DatabaseSessionMiddleware, RateLimitMiddleware
from .outline_client import outline_client


async def on_shutdown(bot: Bot) -> None:
    await outline_client.close()
    await bot.session.close()


async def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    config = load_config()

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(common.router)
    dp.include_router(payments.router)
    dp.include_router(admin.router)

    dp.update.middleware(DatabaseSessionMiddleware())
    dp.message.middleware(RateLimitMiddleware())

    dp.shutdown.register(on_shutdown)

    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
