# Quazar VPN Telegram Bot

Async Telegram-бот на **aiogram 3** для продажи VPN-подписок через Stars и автоматической выдачи ключей Outline.

## 1. Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # создайте файл с переменными (см. ниже)
python -m bot.main
```

## 2. Переменные окружения

Создайте `.env` (либо экспортируйте переменные):

```
BOT_TOKEN=полученный_у_BotFather
ADMIN_ID=ваш_Telegram_ID
PROVIDER_TOKEN=Stars_provider_token_из_BotFather
OUTLINE_API_URL=https://your-outline-server:PORT
OUTLINE_CERT_SHA256=XX:YY:ZZ:...
```

- `OUTLINE_CERT_SHA256` — SHA256-отпечаток TLS-сертификата Outline Manager. Получить можно командой `openssl s_client -connect host:port -showcerts | openssl x509 -noout -fingerprint -sha256`.

## 3. Outline Server

1. Разверните Outline Manager (официальные инструкции [https://getoutline.org/](https://getoutline.org/)).
2. В настройках Manager включите API-доступ и сохраните `Outline API URL` + fingerprint.
3. Убедитесь, что сервер доступен по публичному адресу и порт не блокируется фаерволом.

## 4. Telegram Bot

- Установите команды в BotFather: `/start`, `/my_subscription`, `/admin`, `/broadcast`.
- Stars-платежи активируются через BotFather → Payments → Telegram Stars.
- Бот автоматически:
  - Создаёт пользователя в БД (`SQLite`).
  - Регистрирует платежи.
  - После успешного платежа — создаёт ключ в Outline и отправляет ссылку пользователю.

## 5. Локальное тестирование

1. Запустите бота: `python -m bot.main`.
2. В отдельном терминале проверьте БД: `sqlite3 quazar.db 'select * from subscriptions;'`.
3. Используйте тестовый Stars-провайдер от BotFather для песочницы.

## 6. Деплой на VPS

1. Установите Python 3.11+, Git, tmux/supervisor.
2. Склонируйте репозиторий и установите зависимости (`pip install -r requirements.txt`).
3. Настройте systemd unit или supervisor для автозапуска.
4. Обеспечьте постоянное соединение с Outline API (проверьте firewall).

## 7. Переключение на крипто-платежи (CryptoBot)

1. Зарегистрируйте бота в [@CryptoBot](https://t.me/CryptoBot), получите API токен.
2. Установите SDK `pip install cryptopay-api`.
3. Замените модуль `payments`:
   - Вместо `send_invoice` используйте `CryptoPay.create_invoice`.
   - Получайте Webhook от CryptoBot и валидируйте подписи.
   - После подтверждения платежа вызывайте `outline_client.create_key(...)`.
4. Stars-логика (PreCheckoutQuery/SuccessfulPayment) станет неактуальной — удалите соответствующие хендлеры.

## 8. Безопасность

- Храните `quazar.db` в приватном каталоге, делайте резервные копии.
- Регулярно регенерируйте Outline-ключи для истёкших подписок.
- Добавьте мониторинг ошибок (Sentry/Logtail) при продакшн-запуске.
