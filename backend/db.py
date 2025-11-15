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

def save_new_links(links_with_titles):
    """
    Save new article links to database.
    Returns list of newly added articles.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Get existing URLs
    cur.execute("SELECT url FROM posts")
    existing = {row[0] for row in cur.fetchall()}

    new_articles = []
    for url, title in links_with_titles:
        if url not in existing:
            cur.execute(
                "INSERT INTO posts (url, title) VALUES (?, ?)",
                (url, title)
            )
            new_articles.append({"url": url, "title": title})

    conn.commit()
    conn.close()
    return new_articles

def get_all_links(limit=50):
    """Get all stored articles ordered by creation date (newest first)."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT url, title, created_at FROM posts ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()

    return [
        {
            "url": row[0],
            "title": row[1] or "제목 없음",
            "created_at": row[2]
        }
        for row in rows
    ]

def get_paginated_links(page=1, per_page=20):
    """Get paginated articles ordered by creation date (newest first)."""
    conn = sqlite3.connect(DB_PATH)
    offset = (page - 1) * per_page

    rows = conn.execute(
        "SELECT url, title, created_at FROM posts ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (per_page, offset)
    ).fetchall()
    conn.close()

    return [
        {
            "url": row[0],
            "title": row[1] or "제목 없음",
            "created_at": row[2]
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
            "SELECT url, title, created_at FROM posts WHERE created_at > ? ORDER BY created_at DESC",
            (since_timestamp,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT url, title, created_at FROM posts ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
    conn.close()

    return [
        {
            "url": row[0],
            "title": row[1] or "제목 없음",
            "created_at": row[2]
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
