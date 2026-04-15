from pathlib import Path

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
from app.services.telegram_service import send_telegram_message, telegram_ready
import threading
from app.services.telegram_service import run_bot
from fastapi import FastAPI

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app = FastAPI(title=settings.APP_NAME)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

scheduler = AsyncIOScheduler()
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


def filter_articles(articles, search="", region="", category=""):
    search = search.lower().strip()
    filtered = articles

    if region and region in KEYWORD_MAP:
        region_keywords = [keyword.lower() for keyword in KEYWORD_MAP[region]]
        filtered = [
            article
            for article in filtered
            if any(keyword in f"{article['title']} {article['description']}".lower() for keyword in region_keywords)
        ]

    if search:
        filtered = [
            article
            for article in filtered
            if search in f"{article['title']} {article['description']} {article['source']}".lower()
        ]

    return filtered


async def refresh_news_cache():
    # Refresh everything once, then let the frontend slice and search locally through the API.
    grouped = await fetch_all_articles()
    all_articles = grouped.get("World", [])
    save_articles(all_articles)
    NEWS_CACHE["articles_by_category"] = grouped
    NEWS_CACHE["summary"] = build_daily_summary(all_articles)
    NEWS_CACHE["last_error"] = (
        ""
        if all_articles
        else "No articles were fetched. Check your internet access, verify RSS feeds are reachable on your machine, and add NEWSAPI_KEY in .env for a more reliable fallback."
    )
    return NEWS_CACHE


async def scheduled_telegram_delivery():
    try:
        if not NEWS_CACHE["articles_by_category"].get("World"):
            await refresh_news_cache()
        digest = format_telegram_digest(NEWS_CACHE["summary"])
        await send_telegram_message(digest)
    except Exception as exc:
        NEWS_CACHE["last_error"] = f"Scheduled Telegram delivery failed: {exc}"

@app.on_event("startup")
async def startup_event():
    init_db()

    # 🔥 ADD THIS LINE (VERY IMPORTANT)
    await refresh_news_cache()

    scheduler.add_job(
        scheduled_telegram_delivery,
        "cron",
        hour=settings.DAILY_SUMMARY_HOUR,
        minute=settings.DAILY_SUMMARY_MINUTE,
        id="daily_telegram_summary",
        replace_existing=True,
    )

    scheduler.start()

    threading.Thread(target=run_bot, daemon=True).start()


@app.on_event("shutdown")
async def shutdown_event():
    if scheduler.running:
        scheduler.shutdown()


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


@app.post("/api/refresh")
async def refresh_news():
    try:
        cache = await refresh_news_cache()
        return {"ok": True, "summary": cache["summary"], "message": "News refreshed successfully."}
    except Exception as exc:
        NEWS_CACHE["last_error"] = f"Failed to refresh news: {exc}"
        return JSONResponse(
            status_code=500,
            content={"ok": False, "message": NEWS_CACHE["last_error"]},
        )


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
