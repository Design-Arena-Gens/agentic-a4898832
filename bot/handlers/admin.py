from __future__ import annotations

import asyncio
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from ..config import load_config
from ..services import compute_stats, list_users

logger = logging.getLogger(__name__)
router = Router()
config = load_config()


def is_admin(user_id: int) -> bool:
    return user_id == config.admin_id


@router.message(Command("admin"))
async def admin_dashboard(message: Message, session):
    if not is_admin(message.from_user.id):
        await message.answer("Нет доступа. Это приватная комната боссов.")
        return

    stats = await compute_stats(session)
    text = (
        "📊 Статистика Quazar VPN\n"
        f"Пользователей: {stats['total_users']}\n"
        f"Доход (Stars): {stats['total_revenue_stars']}\n"
        "Держим уровень."
    )
    await message.answer(text)


class BroadcastStates(StatesGroup):
    waiting_for_message = State()


@router.message(Command("broadcast"))
async def start_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Нет доступа.")
        return

    await message.answer("Босс, скинь текст рассылки. Отмена — /cancel.")
    await state.set_state(BroadcastStates.waiting_for_message)


@router.message(Command("cancel"), BroadcastStates.waiting_for_message)
async def cancel_broadcast(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Рассылка отменена.")


@router.message(BroadcastStates.waiting_for_message)
async def process_broadcast(message: Message, state: FSMContext, session):
    if not is_admin(message.from_user.id):
        await message.answer("Нет доступа.")
        return

    await state.clear()
    text = message.text
    users = await list_users(session)
    await message.answer(f"Рассылаю по {len(users)} аккаунтам...")

    sent = 0
    failed = 0
    for user in users:
        try:
            await message.bot.send_message(user.telegram_id, text)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception as exc:  # noqa: BLE001
            failed += 1
            logger.warning("Broadcast failed for user %s: %s", user.telegram_id, exc)

    await message.answer(f"Готово. Отправлено: {sent}, ошибок: {failed}.")
