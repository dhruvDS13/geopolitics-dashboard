from pathlib import Path
import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.database import init_db, save_articles
from app.keywords import CATEGORY_ORDER, KEYWORD_MAP
from app.services.news_service import fetch_all_articles
from app.services.summary_service import build_daily_summary, format_telegram_digest
from app.services.telegram_service import send_telegram_message, telegram_ready, run_bot_async
from telegram import Update
from app.services.telegram_service import telegram_app

BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title=settings.APP_NAME)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


# ✅ Scheduler
scheduler = AsyncIOScheduler()


# ✅ Global Cache
NEWS_CACHE = {
    "articles_by_category": {category: [] for category in CATEGORY_ORDER},
    "summary": {
        "date": "",
        "summary_text": "Refresh the news to build today's digest.",
        "top_stories": [],
        "security_focus": "No focus generated yet.",
    },
    "last_error": "",
}


# ✅ Filter Function
def filter_articles(articles, search="", region="", category=""):
    search = search.lower().strip()
    filtered = articles

    if region and region in KEYWORD_MAP:
        region_keywords = [keyword.lower() for keyword in KEYWORD_MAP[region]]
        filtered = [
            article
            for article in filtered
            if any(
                keyword in f"{article['title']} {article['description']}".lower()
                for keyword in region_keywords
            )
        ]

    if search:
        filtered = [
            article
            for article in filtered
            if search in f"{article['title']} {article['description']} {article['source']}".lower()
        ]

    return filtered


# ✅ Refresh Cache
async def refresh_news_cache():
    print("🔄 Refreshing news cache...")

    try:
        grouped = await fetch_all_articles()
        all_articles = grouped.get("World", [])

        save_articles(all_articles)

        NEWS_CACHE["articles_by_category"] = grouped
        NEWS_CACHE["summary"] = build_daily_summary(all_articles)

        NEWS_CACHE["last_error"] = (
            "" if all_articles else "No articles were fetched. Check RSS/API settings."
        )

    except Exception as e:
        print(f"❌ Error refreshing news: {e}")
        NEWS_CACHE["last_error"] = f"Failed to refresh news: {e}"

    return NEWS_CACHE


# ✅ Scheduled Telegram Delivery
async def scheduled_telegram_delivery():
    try:
        if not NEWS_CACHE["articles_by_category"].get("World"):
            await refresh_news_cache()

        digest = format_telegram_digest(NEWS_CACHE["summary"])
        await send_telegram_message(digest)

    except Exception as exc:
        NEWS_CACHE["last_error"] = f"Scheduled Telegram delivery failed: {exc}"


# ✅ Startup
@app.on_event("startup")
async def startup_event():
    init_db()

    await refresh_news_cache()

    scheduler.add_job(
        scheduled_telegram_delivery,
        "cron",
        hour=settings.DAILY_SUMMARY_HOUR,
        minute=settings.DAILY_SUMMARY_MINUTE,
        id="daily_telegram_summary",
        replace_existing=True,
    )

    if not scheduler.running:
        scheduler.start()

    # 🚀 START TELEGRAM BOT (IMPORTANT)

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    update = Update.de_json(data, telegram_app.bot)

    await telegram_app.initialize()
    await telegram_app.process_update(update)

    return {"ok": True}


# ✅ Shutdown
@app.on_event("shutdown")
async def shutdown_event():
    if scheduler.running:
        scheduler.shutdown()


# ✅ Home Route
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_name": settings.APP_NAME,
            "categories": CATEGORY_ORDER,
        },
    )


# ✅ API: Get News
@app.get("/api/news")
async def get_news(
    search: str = Query(default=""),
    region: str = Query(default=""),
    category: str = Query(default="World"),
):
    if not NEWS_CACHE["articles_by_category"].get("World") and not NEWS_CACHE["last_error"]:
        try:
            await refresh_news_cache()
        except Exception as exc:
            NEWS_CACHE["last_error"] = f"Failed to fetch news: {exc}"

    articles = NEWS_CACHE["articles_by_category"].get(category, [])
    filtered = filter_articles(articles, search=search, region=region, category=category)

    return {
        "articles": filtered,
        "summary": NEWS_CACHE["summary"],
        "error": NEWS_CACHE["last_error"],
        "telegram_configured": telegram_ready(),
    }


# ✅ API: Refresh
@app.post("/api/refresh")
async def refresh_news():
    try:
        cache = await refresh_news_cache()
        return {
            "ok": True,
            "summary": cache["summary"],
            "message": "News refreshed successfully.",
        }
    except Exception as exc:
        NEWS_CACHE["last_error"] = f"Failed to refresh news: {exc}"
        return JSONResponse(
            status_code=500,
            content={"ok": False, "message": NEWS_CACHE["last_error"]},
        )


# ✅ API: Send Telegram
@app.post("/api/send-telegram")
async def send_digest():
    try:
        if not NEWS_CACHE["articles_by_category"].get("World"):
            await refresh_news_cache()

        digest = format_telegram_digest(NEWS_CACHE["summary"])
        result = await send_telegram_message(digest)

        status_code = 200 if result["ok"] else 400
        return JSONResponse(status_code=status_code, content=result)

    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "message": f"Telegram send failed: {exc}"},
        )