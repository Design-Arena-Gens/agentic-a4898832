import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class OutlineConfig:
    api_url: str
    cert_sha256: str
    timeout: int = 10


@dataclass(frozen=True)
class PaymentPlan:
    months: int
    price_rub: int
    price_stars: int
    discount_hint: str | None = None


@dataclass(frozen=True)
class BotConfig:
    bot_token: str
    admin_id: int
    provider_token: str
    outline: OutlineConfig
    database_url: str = "sqlite+aiosqlite:///./quazar.db"
    rate_limit_per_minute: int = 5

    @property
    def plans(self) -> list[PaymentPlan]:
        return [
            PaymentPlan(months=1, price_rub=499, price_stars=499),
            PaymentPlan(months=6, price_rub=2499, price_stars=2499, discount_hint="скидка 16%"),
            PaymentPlan(months=12, price_rub=3999, price_stars=3999, discount_hint="скидка 33%"),
        ]


@lru_cache(maxsize=1)
def load_config() -> BotConfig:
    return BotConfig(
        bot_token=os.getenv("BOT_TOKEN", "your_token"),
        admin_id=int(os.getenv("ADMIN_ID", "123456789")),
        provider_token=os.getenv("PROVIDER_TOKEN", "your_provider_token"),
        outline=OutlineConfig(
            api_url=os.getenv("OUTLINE_API_URL", "https://your-outline-server:PORT"),
            cert_sha256=os.getenv("OUTLINE_CERT_SHA256", "your_cert_sha256"),
        ),
    )
