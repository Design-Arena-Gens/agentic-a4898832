from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import Message, PreCheckoutQuery

from ..outline_client import outline_client
from ..services import (
    create_subscription,
    ensure_user,
    get_payment_by_payload,
    mark_payment_failed,
    mark_payment_success,
    resolve_plan_by_payload,
)

logger = logging.getLogger(__name__)
router = Router()


@router.pre_checkout_query()
async def process_pre_checkout(query: PreCheckoutQuery, session):
    plan = resolve_plan_by_payload(query.invoice_payload)
    if not plan:
        await query.answer(
            ok=False,
            error_message="Тариф не найден. Напиши в поддержку @your_support_username",
        )
        return

    payment = await get_payment_by_payload(session, query.invoice_payload)
    if not payment:
        await query.answer(
            ok=False,
            error_message="Счёт не найден. Попробуй ещё раз оформить тариф.",
        )
        logger.warning("Missing payment record for payload %s", query.invoice_payload)
        return

    await query.answer(ok=True)


@router.message(F.successful_payment)
async def handle_successful_payment(message: Message, session):
    successful_payment = message.successful_payment
    payload = successful_payment.invoice_payload
    plan = resolve_plan_by_payload(payload)
    if not plan:
        await message.answer("Не смог определить тариф. Отпиши в поддержку.")
        logger.error("Unknown plan payload: %s", payload)
        return

    user = await ensure_user(session, message.from_user)
    payment = await get_payment_by_payload(session, payload)
    if not payment:
        await message.answer("Счёт не найден, обратная связь уже летит к админу.")
        logger.error("Payment not found for payload %s", payload)
        return

    try:
        outline_key = await outline_client.create_key(label=f"tg-{user.telegram_id}")
        subscription = await create_subscription(
            session=session,
            user=user,
            outline_key_id=outline_key.key_id,
            outline_access_url=outline_key.access_url,
            months=plan.months,
        )
        await mark_payment_success(session, payment, subscription)
    except Exception as exc:
        await mark_payment_failed(session, payment)
        logger.exception("Failed to create Outline key: payload=%s error=%s", payload, exc)
        await message.answer(
            "Ошибка при выдаче ключа. Сообщил технарям, скоро всё решим."
        )
        return

    text = (
        "Босс, подписка активирована! 🚀\n"
        f"Вот твой ключ:\n{outline_key.access_url}\n\n"
        "Инструкция по подключению:\n"
        "1. Скачай Outline (iOS, Android, Windows, macOS, Linux).\n"
        "2. Открой приложение и вставь ключ выше.\n"
        "3. Включай и лети без ограничений.\n\n"
        "Полная анонимность на скорости света. Если нужна помощь — @your_support_username."
    )
    await message.answer(text)
