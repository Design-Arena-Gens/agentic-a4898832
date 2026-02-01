from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .config import load_config


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Тарифы 💸", callback_data="plans"),
            ],
            [
                InlineKeyboardButton(text="Моя подписка 📱", callback_data="my_subscription"),
            ],
            [
                InlineKeyboardButton(
                    text="Поддержка 🆘",
                    url="https://t.me/your_support_username",
                ),
            ],
        ]
    )


def plans_keyboard() -> InlineKeyboardMarkup:
    config = load_config()
    buttons = []
    for plan in config.plans:
        discount = f" ({plan.discount_hint})" if plan.discount_hint else ""
        text = f"{plan.months} мес — {plan.price_rub}₽{discount}"
        callback_data = f"plan:{plan.months}"
        buttons.append([InlineKeyboardButton(text=text, callback_data=callback_data)])
    buttons.append([InlineKeyboardButton(text="Назад ⬅️", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def renew_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Продлить 🔁", callback_data="plans")],
        ]
    )
