import sqlite3
import os
from datetime import datetime

# DB 경로를 절대 경로로 설정하여 backend 폴더에서 실행하든 root에서 실행하든 동일한 DB 사용
DB_PATH = os.path.join(os.path.dirname(__file__), "articles.db")

def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            url TEXT PRIMARY KEY,
            title TEXT,
            published_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS article_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_url TEXT UNIQUE,
            summary TEXT,
            keywords TEXT,  -- JSON array string
            bible_verses TEXT,  -- JSON array string
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (article_url) REFERENCES posts (url)
        )
    """)
    conn.close()

def save_new_links(links_with_titles_and_dates):
    """
    Save new article links to database.
    links_with_titles_and_dates should be list of tuples: (url, title, published_at)
    Returns list of newly added articles.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Get existing URLs
    cur.execute("SELECT url FROM posts")
    existing = {row[0] for row in cur.fetchall()}

    new_articles = []
    for item in links_with_titles_and_dates:
        if len(item) == 3:
            url, title, published_at = item
        else:
            # Backward compatibility: if no date provided, use None
            url, title = item
            published_at = None

        if url not in existing:
            cur.execute(
                "INSERT INTO posts (url, title, published_at) VALUES (?, ?, ?)",
                (url, title, published_at)
            )
            new_articles.append({"url": url, "title": title, "published_at": published_at})

    conn.commit()
    conn.close()
    return new_articles

def get_all_links(limit=50):
    """Get all stored articles ordered by published date (newest first)."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT url, title, COALESCE(published_at, created_at) as sort_date FROM posts ORDER BY sort_date DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()

    return [
        {
            "url": row[0],
            "title": row[1] or "제목 없음",
            "created_at": row[2]  # API 호환성을 위해 created_at 필드로 유지
        }
        for row in rows
    ]

def get_paginated_links(page=1, per_page=20):
    """Get paginated articles ordered by published date (newest first)."""
    conn = sqlite3.connect(DB_PATH)
    offset = (page - 1) * per_page

    rows = conn.execute(
        "SELECT url, title, COALESCE(published_at, created_at) as sort_date FROM posts ORDER BY sort_date DESC LIMIT ? OFFSET ?",
        (per_page, offset)
    ).fetchall()
    conn.close()

    return [
        {
            "url": row[0],
            "title": row[1] or "제목 없음",
            "created_at": row[2]  # API 호환성을 위해 created_at 필드로 유지
        }
        for row in rows
    ]

def get_total_article_count():
    """Get total count of articles in database."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT COUNT(*) FROM posts").fetchone()
    conn.close()
    return row[0] if row else 0

def get_latest_links(since_timestamp=None):
    """Get articles created after a specific timestamp."""
    conn = sqlite3.connect(DB_PATH)
    if since_timestamp:
        rows = conn.execute(
            "SELECT url, title, COALESCE(published_at, created_at) as sort_date FROM posts WHERE created_at > ? ORDER BY sort_date DESC",
            (since_timestamp,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT url, title, COALESCE(published_at, created_at) as sort_date FROM posts ORDER BY sort_date DESC LIMIT 10"
        ).fetchall()
    conn.close()

    return [
        {
            "url": row[0],
            "title": row[1] or "제목 없음",
            "created_at": row[2]  # API 호환성을 위해 created_at 필드로 유지
        }
        for row in rows
    ]

def save_article_summary(article_url, summary, keywords, bible_verses):
    """Save article summary to database."""
    import json
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Convert arrays to JSON strings
    keywords_json = json.dumps(keywords, ensure_ascii=False)
    bible_verses_json = json.dumps(bible_verses, ensure_ascii=False)

    # Insert or replace summary
    cur.execute("""
        INSERT OR REPLACE INTO article_summaries
        (article_url, summary, keywords, bible_verses)
        VALUES (?, ?, ?, ?)
    """, (article_url, summary, keywords_json, bible_verses_json))

    conn.commit()
    conn.close()

def get_article_summaries(limit=10):
    """Get article summaries with article info."""
    import json
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT s.article_url, p.title, s.summary, s.keywords, s.bible_verses, s.created_at
        FROM article_summaries s
        JOIN posts p ON s.article_url = p.url
        ORDER BY s.created_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()

    summaries = []
    for row in rows:
        try:
            keywords = json.loads(row[3]) if row[3] else []
            bible_verses = json.loads(row[4]) if row[4] else []
        except json.JSONDecodeError:
            keywords = []
            bible_verses = []

        summaries.append({
            "article_url": row[0],
            "title": row[1] or "제목 없음",
            "summary": row[2],
            "keywords": keywords,
            "bible_verses": bible_verses,
            "created_at": row[5]
        })

    return summaries

def get_article_summary(article_url):
    """Get summary for a specific article."""
    import json
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("""
        SELECT s.summary, s.keywords, s.bible_verses, s.created_at
        FROM article_summaries s
        WHERE s.article_url = ?
    """, (article_url,)).fetchone()
    conn.close()

    if row:
        try:
            keywords = json.loads(row[1]) if row[1] else []
            bible_verses = json.loads(row[2]) if row[2] else []
        except json.JSONDecodeError:
            keywords = []
            bible_verses = []

        return {
            "summary": row[0],
            "keywords": keywords,
            "bible_verses": bible_verses,
            "created_at": row[3]
        }
    return None

def migrate_published_dates():
    """
    Migrate existing articles to add published_at dates.
    Uses the scraper to extract publication dates for articles that don't have them.
    """
    from scraper import scrape_article_date

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # published_at이 NULL인 기사들 조회
    cur.execute("SELECT url FROM posts WHERE published_at IS NULL")
    articles_without_dates = [row[0] for row in cur.fetchall()]

    updated_count = 0
    for url in articles_without_dates:
        published_at = scrape_article_date(url)
        if published_at:
            cur.execute(
                "UPDATE posts SET published_at = ? WHERE url = ?",
                (published_at, url)
            )
            updated_count += 1
            print(f"Updated {url} with date {published_at}")
        else:
            print(f"Could not extract date for {url}")

    conn.commit()
    conn.close()
    return updated_count
