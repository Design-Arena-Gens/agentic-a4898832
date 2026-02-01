from __future__ import annotations

import time

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, LabeledPrice, Message

from ..config import load_config
from ..keyboards import main_menu_keyboard, plans_keyboard, renew_keyboard
from ..services import (
    ensure_user,
    format_subscription_message,
    get_active_subscription,
    register_payment,
    resolve_plan_by_payload,
)

router = Router()
config = load_config()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Добро пожаловать в Quazar VPN 🚀\nАнонимность на скорости света. Полная свобода интернета.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("start"))
async def fallback_start(message: Message) -> None:
    await cmd_start(message)


@router.callback_query(F.data == "back_main")
async def back_to_main(call: CallbackQuery) -> None:
    await call.message.edit_text(
        "Выбери свой ход, босс.",
        reply_markup=main_menu_keyboard(),
    )
    await call.answer()


@router.callback_query(F.data == "plans")
async def show_plans(call: CallbackQuery) -> None:
    text_lines = [
        "🔥 Тарифы Quazar VPN:",
        "1 месяц — 499₽",
        "6 месяцев — 2499₽ (скидка 16%)",
        "12 месяцев — 3999₽ (скидка 33%)",
        "",
        "Оплата Stars. Мгновенный доступ после оплаты.",
    ]
    await call.message.edit_text("\n".join(text_lines), reply_markup=plans_keyboard())
    await call.answer("Босс, выбирай мощность.")


@router.callback_query(F.data.startswith("plan:"))
async def select_plan(call: CallbackQuery, session):
    plan_months = int(call.data.split(":")[1])
    plan = next((p for p in config.plans if p.months == plan_months), None)
    if not plan:
        await call.answer("Тариф не найден. Попробуй ещё раз.", show_alert=True)
        return

    user = await ensure_user(session, call.from_user)
    payload = f"plan-{plan.months}m-{user.telegram_id}-{int(time.time())}"
    await register_payment(
        session=session,
        user=user,
        payload=payload,
        stars_amount=plan.price_stars,
        fiat_amount=plan.price_rub,
    )

    prices = [LabeledPrice(label=f"{plan.months} мес Quazar VPN", amount=plan.price_stars)]
    await call.message.answer_invoice(
        title=f"Quazar VPN — {plan.months} мес",
        description="Босс, ты в деле. Анонимный доступ без компромиссов.",
        payload=payload,
        provider_token=config.provider_token,
        currency="XTR",
        prices=prices,
        need_email=False,
        need_name=False,
        start_parameter="quazarvpn",
    )
    await call.answer("Счёт выставлен. Оплачивай и зажигай!")


async def _reply_subscription(user, target, session):
    subscription = await get_active_subscription(session, user.id)
    if not subscription:
        await target.answer(
            "Пока без брони. Активируй защиту — выбери тариф.", reply_markup=plans_keyboard()
        )
        return

    message_text = format_subscription_message(subscription)
    await target.answer(message_text, reply_markup=renew_keyboard())


@router.message(Command("my_subscription"))
async def my_subscription_cmd(message: Message, session):
    user = await ensure_user(session, message.from_user)
    await _reply_subscription(user, message, session)


@router.callback_query(F.data == "my_subscription")
async def my_subscription_cb(call: CallbackQuery, session):
    user = await ensure_user(session, call.from_user)
    await call.answer()
    await call.message.answer("Проверяю твою броню...")
    await _reply_subscription(user, call.message, session)
