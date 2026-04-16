import httpx
import asyncio
import telegram

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from app.config import settings
from app.services.subscriber_service import add_user, get_users
from app.services.summary_service import format_telegram_digest


print("Telegram version:", telegram.__version__)


# ✅ CHECK TOKEN
def telegram_ready() -> bool:
    return bool(settings.TELEGRAM_BOT_TOKEN)


# ✅ SEND MESSAGE TO ALL USERS
async def send_telegram_message(message: str) -> dict:
    if not telegram_ready():
        return {"ok": False, "message": "Telegram token missing"}

    users = get_users()

    if not users:
        return {"ok": False, "message": "No subscribers found"}

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    async with httpx.AsyncClient(timeout=20) as client:
        for user_id in users:
            try:
                await client.post(
                    url,
                    json={
                        "chat_id": user_id,
                        "text": message,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": True,
                    },
                )
            except Exception as e:
                print(f"Telegram error for {user_id}: {e}")
                continue

    return {"ok": True, "message": "Message sent to all users"}


# ✅ /start COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    add_user(user_id)

    await update.message.reply_text(
        "✅ Connected! Sending today's global intelligence brief..."
    )

    try:
        from app.main import NEWS_CACHE

        summary = NEWS_CACHE.get("summary")

        if not summary or not summary.get("top_stories"):
            await update.message.reply_text(
                "⏳ First time loading, please wait and try again in a few seconds."
            )
            return

        message = format_telegram_digest(summary)

        await update.message.reply_text(message)

    except Exception as e:
        print(e)
        await update.message.reply_text(
            "⚠️ Unable to fetch news right now."
        )


# ✅ RUN TELEGRAM BOT (ASYNC + SAFE)
async def run_bot_async():
    try:
        print("🚀 Starting Telegram bot...")

        app = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))

        # ✅ Correct lifecycle (no Updater, no run_polling)
        await app.initialize()
        await app.start()
        await app.bot.initialize()

        print("✅ Telegram bot started successfully")

        # Start polling properly (v20 way)
        await app.start_polling()

    except Exception as e:
        print(f"❌ Telegram bot crash: {e}")