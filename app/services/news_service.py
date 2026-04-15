from asyncio import tasks
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
from http.client import responses
import re
from typing import Any
import asyncio
import feedparser
import httpx

from app.config import settings
from app.keywords import (
    CATEGORY_ORDER,
    INDIA_IMPACT_AREAS,
    KEYWORD_MAP,
    SOURCE_FEEDS,
    STRATEGIC_RELEVANCE_TERMS,
)


def build_or_query(keywords: list[str]) -> str:
    return " OR ".join(f'"{keyword}"' if " " in keyword else keyword for keyword in keywords)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip()).lower()


def article_hash(title: str, url: str) -> str:
    stable_text = f"{normalize_text(title)}|{normalize_text(url.split('?')[0])}"
    return hashlib.sha256(stable_text.encode("utf-8")).hexdigest()


def assign_risk_level(text: str, source_group: str = "") -> str:
    content = normalize_text(text)
    high_terms = ["war", "missile", "attack", "invasion", "homicide", "terror", "airstrike", "nuclear"]
    medium_terms = ["military", "crime", "sanctions", "border", "cartel", "conflict", "naval", "troops"]
    if any(term in content for term in high_terms):
        return "high"
    if source_group in {"global_strategy", "regional_strategy"} and any(term in content for term in medium_terms):
        return "high"
    if any(term in content for term in medium_terms):
        return "medium"
    return "low"


def matches_keywords(article_text: str, keywords: list[str]) -> bool:
    text = normalize_text(article_text)
    return any(normalize_text(keyword) in text for keyword in keywords)


def detect_categories(title: str, description: str) -> list[str]:
    combined = f"{title} {description}"
    categories = ["World"]
    for category, keywords in KEYWORD_MAP.items():
        if category == "World":
            continue
        if matches_keywords(combined, keywords):
            categories.append(category)
    return list(dict.fromkeys(categories))


def select_primary_category(categories: list[str]) -> str:
    for category in categories:
        if category != "World":
            return category
    return "World"


def strategic_score(text: str, source_group: str) -> tuple[bool, float]:
    content = normalize_text(text)
    score = sum(1.0 for term in STRATEGIC_RELEVANCE_TERMS if term in content)
    if source_group in {"india_think_tank", "global_strategy", "regional_strategy"}:
        score += 2.5
    return score >= 2.5, round(min(score, 10.0), 2)


def india_impact_score(text: str) -> tuple[float, str, list[str]]:
    content = normalize_text(text)
    score = 0.0
    reasons = []

    for area, keywords in INDIA_IMPACT_AREAS.items():
        matches = [keyword for keyword in keywords if normalize_text(keyword) in content]
        if matches:
            score += min(len(matches) * 1.4, 3.0)
            reasons.append(area.replace("_", " "))

    if "india" in content:
        score += 2.0
    if "china" in content or "pakistan" in content:
        score += 1.5
    if "hormuz" in content or "oil" in content or "gulf" in content:
        score += 1.25

    score = round(min(score, 10.0), 2)
    if score >= 6.0:
        label = "high"
    elif score >= 3.0:
        label = "medium"
    else:
        label = "low"
    return score, label, list(dict.fromkeys(reasons))


def cluster_label(text: str) -> str:
    content = normalize_text(text)
    if any(term in content for term in ["oil", "gas", "hormuz", "energy", "shipping"]):
        return "Energy and trade security"
    if any(term in content for term in ["china", "indo-pacific", "taiwan", "south china sea", "quad"]):
        return "Indo-Pacific rivalry"
    if any(term in content for term in ["russia", "ukraine", "nato", "europe"]):
        return "European security"
    if any(term in content for term in ["gaza", "iran", "israel", "syria", "lebanon"]):
        return "Middle East conflict"
    if any(term in content for term in ["terror", "crime", "cartel", "gang", "trafficking"]):
        return "Transnational threats"
    return "Broader geopolitical movement"


def enrich_article(article: dict[str, Any], source_meta: dict[str, Any]) -> dict[str, Any]:
    combined = f"{article['title']} {article['description']}"
    strategic_relevance, strategic_value = strategic_score(combined, source_meta.get("group", ""))
    impact_score, impact_label, impact_reasons = india_impact_score(combined)
    article["source_group"] = source_meta.get("group", "global_news")
    article["source_kind"] = source_meta.get("kind", "news_agency")
    article["risk_level"] = assign_risk_level(combined, article["source_group"])
    article["strategic_relevance"] = strategic_relevance
    article["strategic_score"] = strategic_value
    article["india_impact_score"] = impact_score
    article["india_impact_label"] = impact_label
    article["india_impact_reasons"] = impact_reasons
    article["cluster_label"] = cluster_label(combined)
    return article


async def fetch_newsapi_articles(category: str) -> list[dict[str, Any]]:
    if not settings.NEWSAPI_KEY:
        return []

    source_meta = {"group": "global_news", "kind": "news_agency"}
    keywords = KEYWORD_MAP[category]
    from_date = (datetime.now(timezone.utc) - timedelta(hours=settings.DEFAULT_LOOKBACK_HOURS)).isoformat()
    params = {
        "q": build_or_query(keywords),
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": settings.MAX_ARTICLES_PER_TOPIC,
        "from": from_date,
        "apiKey": settings.NEWSAPI_KEY,
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(settings.NEWSAPI_BASE_URL, params=params)
        response.raise_for_status()
        payload = response.json()

    articles = []
    for item in payload.get("articles", []):
        title = item.get("title") or "Untitled article"
        description = item.get("description") or "No description available."
        url = item.get("url") or ""
        if not url:
            continue

        categories = detect_categories(title, description)
        if category not in categories and category != "World":
            continue

        article = {
            "article_hash": article_hash(title, url),
            "title": title,
            "source": (item.get("source") or {}).get("name", "Unknown source"),
            "published_at": item.get("publishedAt", ""),
            "description": description,
            "url": url,
            "image_url": item.get("urlToImage", ""),
            "category": category,
            "matched_categories": categories,
        }
        articles.append(enrich_article(article, source_meta))
    return articles


def parse_feed_date(entry) -> str:
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    if not published:
        return datetime.now(timezone.utc).isoformat()
    return datetime(*published[:6], tzinfo=timezone.utc).isoformat()


async def fetch_rss_articles() -> list[dict[str, Any]]:
    articles = []
    async with httpx.AsyncClient(
        timeout=20,
        follow_redirects=True,
        headers={"User-Agent": "Global-Geopolitics-Tracker/1.0"},
    ) as client:
        
        tasks = [client.get(feed["url"]) for feed in SOURCE_FEEDS]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        for feed, response in zip(SOURCE_FEEDS, responses):
            try:
                if isinstance(response, Exception):
                    continue

                parsed = feedparser.parse(response.content)

            except Exception:
                continue

            if getattr(parsed, "bozo", False) and not parsed.entries:
                continue

            for entry in parsed.entries[: settings.MAX_ARTICLES_PER_TOPIC]:
                title = entry.get("title", "Untitled article")
                description = re.sub(r"<[^>]+>", "", entry.get("summary", "No description available."))
                url = entry.get("link", "")
                if not url:
                    continue

                categories = detect_categories(title, description)
                article = {
                    "article_hash": article_hash(title, url),
                    "title": title,
                    "source": feed["name"],
                    "published_at": parse_feed_date(entry),
                    "description": description,
                    "url": url,
                    "image_url": "",
                    "category": select_primary_category(categories),
                    "matched_categories": categories,
                }
                articles.append(enrich_article(article, feed))
    return articles


def deduplicate_articles(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped = {}
    for article in articles:
        key = article["article_hash"]
        existing = deduped.get(key)
        if not existing:
            deduped[key] = article
            continue

        current_score = article.get("strategic_score", 0) + article.get("india_impact_score", 0)
        existing_score = existing.get("strategic_score", 0) + existing.get("india_impact_score", 0)
        if current_score > existing_score:
            deduped[key] = article
            continue

        if len(article.get("description") or "") > len(existing.get("description") or ""):
            deduped[key] = article
    return list(deduped.values())


def sort_articles(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        articles,
        key=lambda item: (
            item.get("strategic_score", 0),
            item.get("india_impact_score", 0),
            item.get("published_at", ""),
        ),
        reverse=True,
    )


async def fetch_all_articles() -> dict[str, list[dict[str, Any]]]:
    grouped_articles: dict[str, list[dict[str, Any]]] = defaultdict(list)

    newsapi_articles = []
    if settings.NEWSAPI_KEY:
        for category in CATEGORY_ORDER:
            try:
                newsapi_articles.extend(await fetch_newsapi_articles(category))
            except Exception:
                continue

    rss_articles = await fetch_rss_articles() if settings.USE_RSS_FALLBACK else []
    all_articles = sort_articles(deduplicate_articles(newsapi_articles + rss_articles))

    for category in CATEGORY_ORDER:
        if category == "World":
            continue
        grouped_articles[category] = sort_articles(
            [
                article
                for article in all_articles
                if category in article.get("matched_categories", [])
            ]
        )

    grouped_articles["World"] = all_articles
    return grouped_articles
