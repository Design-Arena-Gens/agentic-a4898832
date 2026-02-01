from __future__ import annotations

import datetime as dt
from collections.abc import Sequence

from aiogram.types import User as TelegramUser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import load_config
from .database import Payment, PaymentStatus, Subscription, User


async def ensure_user(session: AsyncSession, tg_user: TelegramUser) -> User:
    stmt = select(User).where(User.telegram_id == tg_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        user.username = tg_user.username
        user.full_name = tg_user.full_name
        return user

    user = User(
        telegram_id=tg_user.id,
        username=tg_user.username,
        full_name=tg_user.full_name,
    )
    session.add(user)
    await session.flush()
    return user


async def get_active_subscription(session: AsyncSession, user_id: int) -> Subscription | None:
    now = dt.datetime.now(dt.timezone.utc)
    stmt = (
        select(Subscription)
        .where(Subscription.user_id == user_id, Subscription.expires_at >= now)
        .order_by(Subscription.expires_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_subscription(
    session: AsyncSession,
    user: User,
    outline_key_id: str,
    outline_access_url: str,
    months: int,
) -> Subscription:
    now = dt.datetime.now(dt.timezone.utc)
    expires_at = now + dt.timedelta(days=30 * months)

    subscription = Subscription(
        user_id=user.id,
        outline_key_id=outline_key_id,
        outline_access_url=outline_access_url,
        months=months,
        expires_at=expires_at,
    )
    session.add(subscription)
    await session.flush()
    return subscription


async def register_payment(
    session: AsyncSession,
    user: User,
    payload: str,
    stars_amount: int,
    fiat_amount: float,
) -> Payment:
    payment = Payment(
        user_id=user.id,
        tg_invoice_payload=payload,
        stars_amount=stars_amount,
        fiat_amount=fiat_amount,
        status=PaymentStatus.PENDING,
    )
    session.add(payment)
    await session.flush()
    return payment


async def get_payment_by_payload(session: AsyncSession, payload: str) -> Payment | None:
    stmt = select(Payment).where(Payment.tg_invoice_payload == payload)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def mark_payment_success(
    session: AsyncSession, payment: Payment, subscription: Subscription
) -> None:
    payment.status = PaymentStatus.SUCCESS
    payment.subscription_id = subscription.id
    await session.flush()


async def mark_payment_failed(session: AsyncSession, payment: Payment) -> None:
    payment.status = PaymentStatus.FAILED
    await session.flush()


async def list_users(session: AsyncSession) -> Sequence[User]:
    result = await session.execute(select(User))
    return result.scalars().all()


async def compute_stats(session: AsyncSession) -> dict[str, int | float]:
    total_users = len((await session.execute(select(User.id))).scalars().all())
    payment_rows = await session.execute(
        select(Payment.stars_amount, Payment.status)
    )
    total_revenue = sum(
        stars for stars, status in payment_rows.all() if status == PaymentStatus.SUCCESS
    )
    return {"total_users": total_users, "total_revenue_stars": total_revenue}


def format_subscription_message(subscription: Subscription) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    days_left = max(0, (subscription.expires_at - now).days)
    expires_at_str = subscription.expires_at.astimezone(dt.timezone(dt.timedelta(hours=3)))  # MSK hint
    return (
        "🔐 Твоя броня активна!\n"
        f"Ключ: {subscription.outline_access_url}\n"
        f"Истекает: {expires_at_str:%d.%m.%Y %H:%M}\n"
        f"Осталось дней: {days_left}"
    )


def resolve_plan_by_payload(payload: str):
    config = load_config()
    for plan in config.plans:
        if payload.startswith(f"plan-{plan.months}m"):
            return plan
    return None
