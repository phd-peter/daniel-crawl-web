import sqlite3
import os
from datetime import datetime

DB_PATH = "articles.db"

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
