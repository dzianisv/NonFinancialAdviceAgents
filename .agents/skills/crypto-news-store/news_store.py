#!/usr/bin/env python3
"""crypto-news-store — local HYBRID news store (SQLite + FTS5 + SimHash near-dup clustering).

The panel must see EVENTS, not articles, and must never re-surface the same news across runs.
This store is the dedup + state layer the `narrative-news` gather seat reads.

Stdlib only (python3 + sqlite3). No network, no embedding model required.

Storage (single SQLite file, default crypto/news/news.db):
  articles  — one row per ingested article (canonical_url + content hash for exact dedup).
  articles_fts (FTS5) — BM25 over title+summary.
  events    — one row per event cluster (near-dup articles collapsed via SimHash), carrying
              first_seen / last_updated / sources(json) / source_count / materiality /
              priced_in / surfaced_to_panel_on  — the cross-run state.

Dedup:
  Layer 1 (exact):  canonical_url OR sha256(normalized(title+summary)) already present -> skip.
  Layer 2 (near):   token-shingle (word + bigram) JACCARD similarity over normalized text; >= threshold
                    (default 0.15) to an existing event -> attach to that event (multi-outlet coverage
                    of ONE event). A 64-bit SimHash is also stored as a coarse signature/representative.
                    Jaccard is the deciding metric because it discriminates SHORT news text (headline +
                    summary) far better than SimHash Hamming distance, which is tuned for long documents.
                    This is the deterministic lexical-semantic fallback for the BM25+dense design when no
                    embedding model is available.

OPTIONAL dense-vector upgrade (graceful):
  Set env CRYPTO_NEWS_EMBED_CMD to a shell command that reads text on stdin and prints a JSON
  float array on stdout. If set AND it works, near-dup uses cosine >= CRYPTO_NEWS_EMBED_COS
  (default 0.85). If the env is absent OR the command fails, we silently fall back to SimHash.
  (True sqlite-vec storage is left as a documented hook; this keeps stdlib-only + never crashes.)

Commands:
  ingest --json <records.json>          idempotent; prints {new, duplicate, events_touched}
  query  --q "<text>" [--days N] [--k N] HYBRID BM25 + near-dup-cluster, fused via RRF; EVENTS out
  new-since --days N                     events with first_seen/last_updated in window AND not yet
                                         surfaced_to_panel_on (the state-aware feed for the panel)
  mark-surfaced --ids id1 id2 ...        stamp surfaced_to_panel_on = today (or --on)
All commands take --db <path> (default crypto/news/news.db) so tests use a throwaway db.
"""
import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import unicodedata
from datetime import datetime, timezone, timedelta

DEFAULT_DB = "crypto/news/news.db"
SIMHASH_BITS = 64
DEFAULT_JACCARD = 0.15        # >= this shingle-Jaccard => same event (near-dup)
SHINGLE = 3                   # token window for SimHash features
JAC_NGRAM = 2                 # word + bigram shingles for Jaccard

# ----------------------------------------------------------------------------- normalization

def normalize_text(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", str(s)).lower()
    s = re.sub(r"https?://\S+", " ", s)
    s = re.sub(r"[^a-z0-9$ ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def content_hash(title, summary):
    return hashlib.sha256(normalize_text(f"{title} {summary}").encode()).hexdigest()


def canonical_url(url):
    if not url:
        return ""
    u = url.strip().split("#")[0]
    u = re.sub(r"[?&](utm_[^=&]+|ref|fbclid|gclid)=[^&]*", "", u)
    return u.rstrip("?&/").lower()


def parse_dt(s):
    """Best-effort parse to aware UTC datetime; None on failure."""
    if not s:
        return None
    s = str(s).strip()
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:  # ISO fallback
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def now_utc():
    return datetime.now(timezone.utc)

# ----------------------------------------------------------------------------- simhash

def _tokens(norm):
    words = norm.split()
    feats = list(words)
    for i in range(len(words) - SHINGLE + 1):
        feats.append(" ".join(words[i:i + SHINGLE]))
    return feats or [norm]


def simhash(norm):
    v = [0] * SIMHASH_BITS
    for tok in _tokens(norm):
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        for b in range(SIMHASH_BITS):
            v[b] += 1 if (h >> b) & 1 else -1
    out = 0
    for b in range(SIMHASH_BITS):
        if v[b] > 0:
            out |= (1 << b)
    return out


def hamming(a, b):
    return bin(a ^ b).count("1")


def shingles(norm, n=JAC_NGRAM):
    w = norm.split()
    s = set(w)
    for i in range(len(w) - n + 1):
        s.add(" ".join(w[i:i + n]))
    return s or {norm}


def jaccard(a, b):
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0

# ----------------------------------------------------------------------------- optional embeddings

def embed(text):
    """Return a float vector via CRYPTO_NEWS_EMBED_CMD, or None if unavailable/failed."""
    cmd = os.environ.get("CRYPTO_NEWS_EMBED_CMD")
    if not cmd:
        return None
    try:
        p = subprocess.run(cmd, shell=True, input=text.encode(),
                           capture_output=True, timeout=30)
        if p.returncode != 0:
            return None
        vec = json.loads(p.stdout.decode())
        return [float(x) for x in vec] if isinstance(vec, list) and vec else None
    except Exception:
        return None


def cosine(a, b):
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0

# ----------------------------------------------------------------------------- schema

def connect(db_path):
    if db_path != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.executescript("""
    CREATE TABLE IF NOT EXISTS events (
        event_cluster_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        rep_simhash        TEXT NOT NULL,          -- representative simhash (decimal string)
        rep_norm           TEXT NOT NULL DEFAULT '',-- normalized rep text (for Jaccard near-dup)
        rep_embedding      TEXT,                   -- optional JSON float array
        title              TEXT NOT NULL,
        first_seen         TEXT NOT NULL,
        last_updated       TEXT NOT NULL,
        sources            TEXT NOT NULL DEFAULT '[]',   -- json list of distinct source names
        source_count       INTEGER NOT NULL DEFAULT 0,
        materiality        TEXT,
        priced_in          TEXT,
        surfaced_to_panel_on TEXT
    );
    CREATE TABLE IF NOT EXISTS articles (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id      INTEGER NOT NULL REFERENCES events(event_cluster_id),
        source        TEXT, url TEXT, title TEXT, summary TEXT,
        published_at  TEXT, lang TEXT, tags TEXT,
        canonical_url TEXT, content_hash TEXT, simhash TEXT,
        ingested_at   TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_art_canon ON articles(canonical_url);
    CREATE INDEX IF NOT EXISTS idx_art_hash  ON articles(content_hash);
    CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts
        USING fts5(title, summary, content='articles', content_rowid='id');
    CREATE TRIGGER IF NOT EXISTS art_ai AFTER INSERT ON articles BEGIN
        INSERT INTO articles_fts(rowid, title, summary) VALUES (new.id, new.title, new.summary);
    END;
    """)
    return con

# ----------------------------------------------------------------------------- ingest

def find_event(con, sh, norm, emb):
    """Return existing event row to attach to (near-dup), or None.

    Decision metric is shingle-Jaccard (best for short news text). The optional dense-embedding
    path, when configured and available, takes precedence (cosine >= threshold)."""
    rows = con.execute("SELECT * FROM events").fetchall()
    cos_thr = float(os.environ.get("CRYPTO_NEWS_EMBED_COS", "0.85"))
    jac_thr = float(os.environ.get("CRYPTO_NEWS_JACCARD", str(DEFAULT_JACCARD)))
    qsh = shingles(norm)
    best = None
    for r in rows:
        if emb is not None and r["rep_embedding"]:
            try:
                if cosine(emb, json.loads(r["rep_embedding"])) >= cos_thr:
                    return r
            except Exception:
                pass
        j = jaccard(qsh, shingles(r["rep_norm"]))
        if j >= jac_thr and (best is None or j > best[1]):
            best = (r, j)
    return best[0] if best else None


def ingest(con, records):
    new = dup = touched = 0
    ts = now_utc().isoformat()
    for rec in records:
        title = (rec.get("title") or "").strip()
        summary = (rec.get("summary") or rec.get("body") or "").strip()
        if not title:
            continue
        curl = canonical_url(rec.get("url"))
        chash = content_hash(title, summary)
        # ---- Layer 1: exact dedup
        exists = con.execute(
            "SELECT 1 FROM articles WHERE content_hash=? OR (canonical_url<>'' AND canonical_url=?) LIMIT 1",
            (chash, curl)).fetchone()
        if exists:
            dup += 1
            continue
        norm = normalize_text(f"{title} {summary}")
        sh = simhash(norm)
        emb = embed(f"{title}. {summary}")
        src = (rec.get("source") or "").strip() or "unknown"
        pub = rec.get("published_at") or ts
        # ---- Layer 2: near-dup clustering
        ev = find_event(con, sh, norm, emb)
        if ev is None:
            cur = con.execute(
                "INSERT INTO events(rep_simhash, rep_norm, rep_embedding, title, first_seen, last_updated,"
                " sources, source_count, materiality, priced_in) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (str(sh), norm, json.dumps(emb) if emb else None, title, pub, ts,
                 json.dumps([src]), 1, rec.get("materiality"), rec.get("priced_in")))
            event_id = cur.lastrowid
        else:
            event_id = ev["event_cluster_id"]
            srcs = json.loads(ev["sources"])
            if src not in srcs:
                srcs.append(src)
            con.execute(
                "UPDATE events SET last_updated=?, sources=?, source_count=? WHERE event_cluster_id=?",
                (ts, json.dumps(srcs), len(srcs), event_id))
            touched += 1
        con.execute(
            "INSERT INTO articles(event_id, source, url, title, summary, published_at, lang, tags,"
            " canonical_url, content_hash, simhash, ingested_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (event_id, src, rec.get("url"), title, summary, pub, rec.get("lang"),
             json.dumps(rec.get("tags") or []), curl, chash, str(sh), ts))
        new += 1
    con.commit()
    return {"new": new, "duplicate": dup, "events_touched": touched}

# ----------------------------------------------------------------------------- query / feed

def _event_dict(con, r):
    return {
        "event_cluster_id": r["event_cluster_id"],
        "title": r["title"],
        "first_seen": r["first_seen"],
        "last_updated": r["last_updated"],
        "sources": json.loads(r["sources"]),
        "source_count": r["source_count"],
        "materiality": r["materiality"],
        "priced_in": r["priced_in"],
        "surfaced_to_panel_on": r["surfaced_to_panel_on"],
    }


def query(con, q, days=None, k=10):
    """HYBRID retrieval: FTS5/BM25 ranking + near-dup cluster recency, fused via RRF -> EVENTS."""
    norm = normalize_text(q)
    # rank A: BM25 over articles -> map to events (best article rank per event)
    bm25_events = []
    seen = set()
    try:
        rows = con.execute(
            "SELECT a.event_id AS eid FROM articles_fts f JOIN articles a ON a.id=f.rowid"
            " WHERE articles_fts MATCH ? ORDER BY bm25(articles_fts) LIMIT 200",
            (norm or q,)).fetchall()
    except sqlite3.OperationalError:
        rows = []
    for r in rows:
        if r["eid"] not in seen:
            seen.add(r["eid"]); bm25_events.append(r["eid"])
    # rank B: shingle-Jaccard similarity of the query to each event's representative (lexical-semantic)
    qsh = shingles(norm)
    ev_rows = con.execute("SELECT * FROM events").fetchall()
    sim_events = sorted(ev_rows, key=lambda r: -jaccard(qsh, shingles(r["rep_norm"])))
    sim_rank = [r["event_cluster_id"] for r in sim_events]
    # RRF fusion
    KK = 60
    score = {}
    for rank, eid in enumerate(bm25_events):
        score[eid] = score.get(eid, 0) + 1.0 / (KK + rank + 1)
    for rank, eid in enumerate(sim_rank):
        score[eid] = score.get(eid, 0) + 1.0 / (KK + rank + 1)
    by_id = {r["event_cluster_id"]: r for r in ev_rows}
    cutoff = now_utc() - timedelta(days=days) if days else None
    out = []
    for eid, sc in sorted(score.items(), key=lambda x: -x[1]):
        r = by_id.get(eid)
        if r is None:
            continue
        if cutoff:
            lu = parse_dt(r["last_updated"]) or now_utc()
            if lu < cutoff:
                continue
        d = _event_dict(con, r); d["score"] = round(sc, 5)
        out.append(d)
        if len(out) >= k:
            break
    return out


def new_since(con, days):
    cutoff = now_utc() - timedelta(days=days)
    rows = con.execute("SELECT * FROM events WHERE surfaced_to_panel_on IS NULL").fetchall()
    out = []
    for r in rows:
        fs = parse_dt(r["first_seen"]) or now_utc()
        lu = parse_dt(r["last_updated"]) or now_utc()
        if fs >= cutoff or lu >= cutoff:
            out.append(_event_dict(con, r))
    out.sort(key=lambda e: e["last_updated"], reverse=True)
    return out


def mark_surfaced(con, ids, on=None):
    on = on or now_utc().date().isoformat()
    n = 0
    for i in ids:
        cur = con.execute(
            "UPDATE events SET surfaced_to_panel_on=? WHERE event_cluster_id=? AND surfaced_to_panel_on IS NULL",
            (on, int(i)))
        n += cur.rowcount
    con.commit()
    return {"marked": n, "on": on}

# ----------------------------------------------------------------------------- cli

def main():
    ap = argparse.ArgumentParser(description="crypto-news-store hybrid news store")
    ap.add_argument("--db", default=os.environ.get("CRYPTO_NEWS_DB", DEFAULT_DB))
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("ingest"); p.add_argument("--json", required=True)
    p = sub.add_parser("query"); p.add_argument("--q", required=True)
    p.add_argument("--days", type=int); p.add_argument("--k", type=int, default=10)
    p = sub.add_parser("new-since"); p.add_argument("--days", type=int, default=2)
    p = sub.add_parser("mark-surfaced"); p.add_argument("--ids", nargs="+", required=True)
    p.add_argument("--on")

    a = ap.parse_args()
    con = connect(a.db)
    if a.cmd == "ingest":
        with open(a.json) as f:
            recs = json.load(f)
        if isinstance(recs, dict):
            recs = recs.get("records") or recs.get("articles") or [recs]
        print(json.dumps(ingest(con, recs), indent=2))
    elif a.cmd == "query":
        print(json.dumps(query(con, a.q, days=a.days, k=a.k), indent=2))
    elif a.cmd == "new-since":
        print(json.dumps(new_since(con, a.days), indent=2))
    elif a.cmd == "mark-surfaced":
        print(json.dumps(mark_surfaced(con, a.ids, on=a.on), indent=2))


if __name__ == "__main__":
    main()
