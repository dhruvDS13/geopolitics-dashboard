from collections import Counter
from datetime import datetime


def build_daily_summary(articles: list[dict]) -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    display_date = datetime.now().strftime("%d-%m-%Y")
    todays_articles = [
        article for article in articles if (article.get("published_at") or "").startswith(today)
    ]
    source_counts = Counter(article["source"] for article in todays_articles)
    risk_counts = Counter(article["risk_level"] for article in todays_articles)
    india_impact_counts = Counter(article.get("india_impact_label", "low") for article in todays_articles)

    
# New logic to limit to 3 articles per source in top stories, while still prioritizing by strategic score, India impact, and risk level
    sorted_articles = sorted(
    todays_articles,
    key=lambda item: (
        item.get("strategic_score", 0),
        item.get("india_impact_score", 0),
        {"high": 3, "medium": 2, "low": 1}.get(item.get("risk_level", "low"), 1),
        item.get("published_at", ""),
    ),
    reverse=True,
    )

    source_count = {}
    top_stories = []

    for article in sorted_articles:
        source = article["source"]

        if source_count.get(source, 0) >= 3:
            continue

        top_stories.append(article)
        source_count[source] = source_count.get(source, 0) + 1

        if len(top_stories) == 10:
            break

    strategic_articles = [article for article in todays_articles if article.get("strategic_relevance")]
    india_sensitive = [article for article in todays_articles if article.get("india_impact_score", 0) >= 4]

    focus = (
        f"{top_stories[0]['title']}"
        if top_stories
        else "No major security event was found yet today."
    )

    india_focus = (
        f"{india_sensitive[0]['title']} ({india_sensitive[0]['india_impact_label'].title()} impact)"
        if india_sensitive
        else "No major India-linked strategic pressure was detected yet today."
    )

    lines = []

    if todays_articles:
        lines.append(f"{len(todays_articles)} global news updates collected today.")
    else:
        lines.append("No global developments detected yet today.")

    metrics = {
        "articles_today": len(todays_articles),
        "high_risk_count": risk_counts.get("high", 0),
        "active_sources": len(source_counts),
        "strategic_count": len(strategic_articles),
        "india_impact_high": india_impact_counts.get("high", 0),
        "avg_india_impact": round(
            sum(article.get("india_impact_score", 0) for article in todays_articles) / len(todays_articles), 2
        ) if todays_articles else 0,
    }

    return {
        "date":  display_date,
        "summary_text": " ".join(lines),
        "top_stories": top_stories,
        "security_focus": focus,
        "india_focus": india_focus,
        "metrics": metrics,
    }

    
def format_telegram_digest(summary: dict) -> str:
    date = summary["date"]
    stories = summary["top_stories"]

    message_lines = [
        f"🌍 GLOBAL NEWS BRIEF",
        f"📅 {date}",
        "",
    ]

    if stories:
        for index, article in enumerate(stories, start=1):
            message_lines.append(f"{index}. {article['title']}")
            message_lines.append("")
    else:
        message_lines.append("No major global developments detected today.")

    return "\n".join(message_lines)
