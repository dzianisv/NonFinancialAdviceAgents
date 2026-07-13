"""
trend-stock-research: SQLite + FTS5/BM25 article store.

IMPORTANT — scope: this module is NOT a general news-fetch/discovery path. It never fetches
anything itself. It only stores and searches agent-curated theme/company/signal tags for
articles that were ALREADY discovered via the shared `read-news` skill
(`read_news.ts`/`feeds/ft.ts`/`feeds/wsj.ts`/`read_news.ts --source googlenews`). Raw news
discovery and search must go through read-news (`read_news.ts`, `news_store.ts query`), never
through this module's `search()` as a discovery mechanism.

This module is kept live (not migrated/deleted) specifically because `search_theme_convergence()`
groups by the `articles.themes` tag column to power multi-week thesis/conviction tracking
(`theses`/`thesis_evidence` tables) — a feature read-news's schema has no equivalent for. Deleting
the `articles` table or its `ingest_article`/`search`/`get_articles_for_theme` functions would
break thesis convergence detection, so full migration to `news_store.ts` was evaluated and
rejected as unsafe within this task's scope.

Zero-cost alternative to vector DB. Financial journalism uses consistent
domain vocabulary ("bottleneck", "capacity constrained", "supply shortage")
so BM25 keyword search works as well as semantic search — no embeddings needed.

DB location: <repo_root>/.cache/stocks-trend-screener/articles.db
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime, date
from typing import Optional


def _find_repo_root() -> Path:
    """Walk up from this file's location until a .git directory is found."""
    p = Path(__file__).resolve()
    for parent in [p] + list(p.parents):
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not find repo root (no .git found up from %s)" % __file__)


DB_DIR = _find_repo_root() / ".cache" / "stocks-trend-screener"
DB_PATH = DB_DIR / "articles.db"


def get_db() -> sqlite3.Connection:
    """Get or create the research database."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    _ensure_schema(db)
    return db


def _ensure_schema(db: sqlite3.Connection):
    """Create tables if they don't exist."""
    db.executescript("""
        -- Core article store
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT NOT NULL,
            source TEXT NOT NULL,          -- 'ft', 'wsj', 'sa', 'edgar', 'reuters', etc.
            date_published DATE,
            date_ingested DATETIME DEFAULT CURRENT_TIMESTAMP,
            body_text TEXT,                 -- full extracted text (may be truncated)
            summary TEXT,                   -- agent-generated 2-3 sentence summary
            themes TEXT,                    -- comma-separated: 'ai-power,transformers,goes'
            companies TEXT,                 -- comma-separated tickers: 'CLF,GEV,ECL'
            signals TEXT,                   -- comma-separated: 'demand_inflection,bottleneck,insider_buy'
            confidence TEXT DEFAULT 'low'   -- 'high','medium','low' (source quality)
        );

        -- FTS5 index for BM25 search over articles
        CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
            title,
            body_text,
            summary,
            themes,
            companies,
            content='articles',
            content_rowid='id',
            tokenize='porter unicode61'     -- porter stemming for English
        );

        -- Triggers to keep FTS in sync
        CREATE TRIGGER IF NOT EXISTS articles_ai AFTER INSERT ON articles BEGIN
            INSERT INTO articles_fts(rowid, title, body_text, summary, themes, companies)
            VALUES (new.id, new.title, new.body_text, new.summary, new.themes, new.companies);
        END;

        CREATE TRIGGER IF NOT EXISTS articles_ad AFTER DELETE ON articles BEGIN
            INSERT INTO articles_fts(articles_fts, rowid, title, body_text, summary, themes, companies)
            VALUES ('delete', old.id, old.title, old.body_text, old.summary, old.themes, old.companies);
        END;

        CREATE TRIGGER IF NOT EXISTS articles_au AFTER UPDATE ON articles BEGIN
            INSERT INTO articles_fts(articles_fts, rowid, title, body_text, summary, themes, companies)
            VALUES ('delete', old.id, old.title, old.body_text, old.summary, old.themes, old.companies);
            INSERT INTO articles_fts(rowid, title, body_text, summary, themes, companies)
            VALUES (new.id, new.title, new.body_text, new.summary, new.themes, new.companies);
        END;

        -- Thesis tracking (accumulated signal → conviction)
        CREATE TABLE IF NOT EXISTS theses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            theme TEXT NOT NULL,
            thesis_text TEXT NOT NULL,
            status TEXT DEFAULT 'monitoring',   -- monitoring, building, actionable, killed, realized
            confidence TEXT DEFAULT 'low',
            created_date DATE DEFAULT CURRENT_DATE,
            updated_date DATE DEFAULT CURRENT_DATE,
            signal_count INTEGER DEFAULT 1,
            source_count INTEGER DEFAULT 1,     -- distinct sources
            week_span INTEGER DEFAULT 1,
            kill_reason TEXT,
            price_at_creation REAL,
            price_current REAL
        );

        -- Evidence links: which articles support which thesis
        CREATE TABLE IF NOT EXISTS thesis_evidence (
            thesis_id INTEGER REFERENCES theses(id),
            article_id INTEGER REFERENCES articles(id),
            relevance TEXT,                     -- 'primary', 'supporting', 'contradicting'
            added_date DATE DEFAULT CURRENT_DATE,
            PRIMARY KEY (thesis_id, article_id)
        );

        -- Daily run log (prevents re-processing)
        CREATE TABLE IF NOT EXISTS run_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date DATE DEFAULT CURRENT_DATE,
            mode TEXT NOT NULL,                -- 'ingest', 'synthesize'
            articles_added INTEGER DEFAULT 0,
            theses_updated INTEGER DEFAULT 0,
            notes TEXT
        );
    """)
    db.commit()


# ─── INGEST API ───────────────────────────────────────────────────────────────

def ingest_article(
    url: str,
    title: str,
    source: str,
    body_text: str,
    summary: str = "",
    themes: str = "",
    companies: str = "",
    signals: str = "",
    confidence: str = "low",
    date_published: Optional[str] = None,
) -> int:
    """Insert an article. Returns rowid. Skips if URL already exists."""
    db = get_db()
    try:
        cur = db.execute("""
            INSERT INTO articles (url, title, source, body_text, summary, themes, companies, signals, confidence, date_published)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (url, title, source, body_text, summary, themes, companies, signals, confidence, date_published))
        db.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        # URL already exists — update instead
        db.execute("""
            UPDATE articles SET body_text=?, summary=?, themes=?, companies=?, signals=?, confidence=?
            WHERE url=?
        """, (body_text, summary, themes, companies, signals, confidence, url))
        db.commit()
        row = db.execute("SELECT id FROM articles WHERE url=?", (url,)).fetchone()
        return row["id"] if row else -1


# ─── SEARCH API ───────────────────────────────────────────────────────────────

# Searches ONLY this skill's own ingested/tagged article corpus (populated by
# ingest_article() from articles fetched via read-news). For raw/fresh news discovery
# not yet ingested here, use read-news's `news_store.ts query` instead — this function
# does not fetch anything.
def search(query: str, limit: int = 20, days_back: int = 90) -> list[dict]:
    """BM25 search over articles. Returns ranked results."""
    db = get_db()
    cutoff = (datetime.now().date().isoformat()
              if days_back <= 0
              else None)

    sql = """
        SELECT a.*, rank
        FROM articles_fts f
        JOIN articles a ON a.id = f.rowid
        WHERE articles_fts MATCH ?
    """
    params = [query]

    if days_back > 0:
        sql += " AND a.date_ingested >= date('now', ?)"
        params.append(f"-{days_back} days")

    sql += " ORDER BY rank LIMIT ?"
    params.append(limit)

    rows = db.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def search_theme_convergence(min_sources: int = 3, min_weeks: int = 2) -> list[dict]:
    """Find themes mentioned by multiple independent sources over multiple weeks.
    This is the CONVERGENCE signal — the core of the stateful advantage."""
    db = get_db()
    rows = db.execute("""
        SELECT
            themes,
            COUNT(DISTINCT source) as source_count,
            COUNT(*) as article_count,
            CAST((julianday('now') - julianday(MIN(date_ingested))) / 7 AS INTEGER) + 1 as week_span,
            GROUP_CONCAT(DISTINCT companies) as all_companies,
            MIN(date_ingested) as first_seen,
            MAX(date_ingested) as last_seen
        FROM articles
        WHERE themes != '' AND date_ingested >= date('now', '-90 days')
        GROUP BY themes
        HAVING COUNT(DISTINCT source) >= ? AND week_span >= ?
        ORDER BY source_count * week_span DESC
    """, (min_sources, min_weeks)).fetchall()
    return [dict(r) for r in rows]


def get_articles_for_theme(theme: str, limit: int = 20) -> list[dict]:
    """Get all articles mentioning a theme, most recent first."""
    db = get_db()
    rows = db.execute("""
        SELECT * FROM articles
        WHERE themes LIKE ?
        ORDER BY date_ingested DESC
        LIMIT ?
    """, (f"%{theme}%", limit)).fetchall()
    return [dict(r) for r in rows]


# ─── THESIS API ───────────────────────────────────────────────────────────────

def upsert_thesis(ticker: str, theme: str, thesis_text: str,
                  confidence: str = "low", article_id: Optional[int] = None) -> int:
    """Create or update a thesis. Links article as evidence if provided."""
    db = get_db()

    existing = db.execute(
        "SELECT id, signal_count, source_count FROM theses WHERE ticker=? AND theme=? AND status NOT IN ('killed','realized')",
        (ticker, theme)
    ).fetchone()

    if existing:
        db.execute("""
            UPDATE theses SET
                signal_count = signal_count + 1,
                updated_date = CURRENT_DATE,
                thesis_text = ?,
                confidence = ?
            WHERE id = ?
        """, (thesis_text, confidence, existing["id"]))
        thesis_id = existing["id"]
    else:
        cur = db.execute("""
            INSERT INTO theses (ticker, theme, thesis_text, confidence)
            VALUES (?, ?, ?, ?)
        """, (ticker, theme, thesis_text, confidence))
        thesis_id = cur.lastrowid

    if article_id:
        db.execute("""
            INSERT OR IGNORE INTO thesis_evidence (thesis_id, article_id, relevance)
            VALUES (?, ?, 'primary')
        """, (thesis_id, article_id))

    db.commit()
    return thesis_id


def get_active_theses() -> list[dict]:
    """Get all non-killed, non-realized theses ordered by signal strength."""
    db = get_db()
    rows = db.execute("""
        SELECT t.*,
            (SELECT COUNT(*) FROM thesis_evidence WHERE thesis_id = t.id) as evidence_count
        FROM theses t
        WHERE t.status NOT IN ('killed', 'realized')
        ORDER BY t.signal_count * t.source_count DESC
    """).fetchall()
    return [dict(r) for r in rows]


def promote_thesis(thesis_id: int, new_status: str):
    """Promote a thesis: monitoring → building → actionable."""
    db = get_db()
    db.execute("UPDATE theses SET status=?, updated_date=CURRENT_DATE WHERE id=?",
               (new_status, thesis_id))
    db.commit()


def kill_thesis(thesis_id: int, reason: str):
    """Kill a thesis with a stated reason."""
    db = get_db()
    db.execute("UPDATE theses SET status='killed', kill_reason=?, updated_date=CURRENT_DATE WHERE id=?",
               (reason, thesis_id))
    db.commit()


# ─── STATS ────────────────────────────────────────────────────────────────────

def stats() -> dict:
    """Return DB stats for the agent to display."""
    db = get_db()
    return {
        "total_articles": db.execute("SELECT COUNT(*) FROM articles").fetchone()[0],
        "articles_this_week": db.execute(
            "SELECT COUNT(*) FROM articles WHERE date_ingested >= date('now', '-7 days')"
        ).fetchone()[0],
        "active_theses": db.execute(
            "SELECT COUNT(*) FROM theses WHERE status NOT IN ('killed','realized')"
        ).fetchone()[0],
        "actionable_theses": db.execute(
            "SELECT COUNT(*) FROM theses WHERE status='actionable'"
        ).fetchone()[0],
        "distinct_sources": db.execute(
            "SELECT COUNT(DISTINCT source) FROM articles"
        ).fetchone()[0],
        "themes_converging": db.execute("""
            SELECT COUNT(*) FROM (
                SELECT themes FROM articles
                WHERE themes != '' AND date_ingested >= date('now', '-90 days')
                GROUP BY themes
                HAVING COUNT(DISTINCT source) >= 3
            )
        """).fetchone()[0],
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: research_db.py <command> [args]")
        print("Commands: init, stats, search <query>, themes, theses")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init":
        db = get_db()
        print(f"Database initialized at {DB_PATH}")
        print(json.dumps(stats(), indent=2))

    elif cmd == "stats":
        print(json.dumps(stats(), indent=2))

    elif cmd == "search":
        q = " ".join(sys.argv[2:])
        results = search(q)
        for r in results:
            print(f"[{r['source']}] {r['title']} ({r['date_published'] or 'no date'})")
            if r.get('summary'):
                print(f"  → {r['summary']}")
            print()

    elif cmd == "themes":
        convergent = search_theme_convergence()
        if not convergent:
            print("No converging themes yet (need 3+ sources over 2+ weeks)")
        for t in convergent:
            print(f"THEME: {t['themes']} — {t['source_count']} sources, {t['week_span']} weeks, {t['article_count']} articles")
            print(f"  Companies: {t['all_companies']}")
            print()

    elif cmd == "theses":
        active = get_active_theses()
        if not active:
            print("No active theses")
        for t in active:
            print(f"[{t['status'].upper()}] {t['ticker']} — {t['theme']} (signals: {t['signal_count']}, confidence: {t['confidence']})")
            print(f"  {t['thesis_text'][:120]}")
            print()

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
