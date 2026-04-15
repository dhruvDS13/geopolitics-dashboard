import sqlite3
import os
from contextlib import contextmanager

from app.config import settings


CREATE_ARTICLES_TABLE = """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_hash TEXT UNIQUE,
    title TEXT NOT NULL,
    source TEXT,
    source_group TEXT,
    source_kind TEXT,
    published_at TEXT,
    description TEXT,
    url TEXT NOT NULL,
    image_url TEXT,
    category TEXT,
    risk_level TEXT,
    strategic_relevance INTEGER DEFAULT 0,
    strategic_score REAL DEFAULT 0,
    india_impact_score REAL DEFAULT 0,
    india_impact_label TEXT,
    india_impact_reasons TEXT,
    cluster_label TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

EXPECTED_COLUMNS = {
    "source_group": "TEXT",
    "source_kind": "TEXT",
    "strategic_relevance": "INTEGER DEFAULT 0",
    "strategic_score": "REAL DEFAULT 0",
    "india_impact_score": "REAL DEFAULT 0",
    "india_impact_label": "TEXT",
    "india_impact_reasons": "TEXT",
    "cluster_label": "TEXT",
}


@contextmanager
def get_connection():
    db_dir = os.path.dirname(settings.DATABASE_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    connection = sqlite3.connect(settings.DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()

def ensure_columns(connection):
    existing = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(articles)").fetchall()
    }
    for column_name, column_type in EXPECTED_COLUMNS.items():
        if column_name not in existing:
            connection.execute(f"ALTER TABLE articles ADD COLUMN {column_name} {column_type}")


def init_db():
    with get_connection() as connection:
        connection.execute(CREATE_ARTICLES_TABLE)
        ensure_columns(connection)


def save_articles(articles):
    if not articles:
        return 0

    inserted = 0
    with get_connection() as connection:
        ensure_columns(connection)
        for article in articles:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO articles
                (
                    article_hash, title, source, source_group, source_kind, published_at, description,
                    url, image_url, category, risk_level, strategic_relevance, strategic_score,
                    india_impact_score, india_impact_label, india_impact_reasons, cluster_label
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    article["article_hash"],
                    article["title"],
                    article["source"],
                    article.get("source_group", ""),
                    article.get("source_kind", ""),
                    article["published_at"],
                    article["description"],
                    article["url"],
                    article["image_url"],
                    article["category"],
                    article["risk_level"],
                    1 if article.get("strategic_relevance") else 0,
                    article.get("strategic_score", 0),
                    article.get("india_impact_score", 0),
                    article.get("india_impact_label", ""),
                    ", ".join(article.get("india_impact_reasons", [])),
                    article.get("cluster_label", ""),
                ),
            )
            inserted += cursor.rowcount
    return inserted
