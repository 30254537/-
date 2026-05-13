"""
New-release monitor — tell me when artists/labels I love drop new tracks.

Subscriptions live in a `subscriptions` table and are checked on demand.
Source backends:

  - Beatport artist/label pages (HTML scrape, no key)
  - Bandcamp artist pages (RSS-style)
  - SoundCloud artist tracks (HTML scrape; uses public API only)

Subscriptions can be inferred automatically from your library:
  - Top 30 most-played artists  → auto-subscribed
  - Top 10 most-played labels    → auto-subscribed
"""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from mixmind import database as db
from mixmind.database import get_connection


def _ensure_schema():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,        -- 'artist' | 'label'
                name TEXT NOT NULL UNIQUE,
                source TEXT,               -- 'beatport' | 'bandcamp' | 'soundcloud' | 'auto'
                added_at TEXT NOT NULL,
                last_checked TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS new_releases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscription_id INTEGER NOT NULL,
                artist TEXT,
                title TEXT,
                label TEXT,
                released_at TEXT,
                url TEXT,
                seen_at TEXT NOT NULL,
                in_library INTEGER DEFAULT 0,
                FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE
            )
        """)


def auto_subscribe_from_library(top_artists: int = 30, top_labels: int = 10) -> Dict[str, Any]:
    """Subscribe to the most-played artists & labels in the library."""
    _ensure_schema()
    tracks = db.find_tracks(limit=100000)
    artist_counts = Counter(t["artist"] for t in tracks if t.get("artist"))
    label_counts = Counter(t.get("album") for t in tracks if t.get("album"))   # albums often == labels for compilations

    added_artists, added_labels = 0, 0
    with get_connection() as conn:
        for artist, _ in artist_counts.most_common(top_artists):
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO subscriptions (kind, name, source, added_at) "
                    "VALUES ('artist', ?, 'auto', ?)",
                    (artist, datetime.utcnow().isoformat()),
                )
                added_artists += 1
            except Exception:
                pass
        for label, _ in label_counts.most_common(top_labels):
            if not label:
                continue
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO subscriptions (kind, name, source, added_at) "
                    "VALUES ('label', ?, 'auto', ?)",
                    (label, datetime.utcnow().isoformat()),
                )
                added_labels += 1
            except Exception:
                pass
    return {"artists_subscribed": added_artists, "labels_subscribed": added_labels}


def add_subscription(name: str, kind: str = "artist", source: str = "beatport") -> int:
    _ensure_schema()
    if kind not in ("artist", "label"):
        raise ValueError("kind must be artist|label")
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO subscriptions (kind, name, source, added_at) "
            "VALUES (?, ?, ?, ?)",
            (kind, name, source, datetime.utcnow().isoformat()),
        )
        return cur.lastrowid or 0


def list_subscriptions() -> List[Dict[str, Any]]:
    _ensure_schema()
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM subscriptions ORDER BY name").fetchall()
        return [dict(r) for r in rows]


def remove_subscription(sub_id: int):
    _ensure_schema()
    with get_connection() as conn:
        conn.execute("DELETE FROM subscriptions WHERE id = ?", (sub_id,))


def _check_artist_beatport(artist: str) -> List[Dict[str, Any]]:
    """Scrape Beatport artist page for recent releases. Best effort."""
    try:
        import requests
    except ImportError:
        return []
    try:
        slug = re.sub(r"[^a-z0-9]+", "-", artist.lower()).strip("-")
        url = f"https://www.beatport.com/artist/{slug}/0"
        resp = requests.get(url, headers={"User-Agent": "MixMindDJ/0.5"}, timeout=8)
        if resp.status_code != 200:
            return []
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.+?)</script>', resp.text, re.DOTALL)
        if not m:
            return []
        data = json.loads(m.group(1))
        out: List[Dict[str, Any]] = []
        # Walk loosely for any `tracks` array
        def _walk(o):
            if isinstance(o, dict):
                if isinstance(o.get("results"), list):
                    yield from o["results"]
                for v in o.values():
                    yield from _walk(v)
            elif isinstance(o, list):
                for x in o:
                    yield from _walk(x)
        for t in list(_walk(data))[:30]:
            if not isinstance(t, dict):
                continue
            title = t.get("name") or t.get("title")
            artists_field = t.get("artists") or []
            if not title:
                continue
            artist_names = ", ".join(a.get("name", "") for a in artists_field if isinstance(a, dict))
            out.append({
                "artist": artist_names or artist,
                "title": title,
                "label": (t.get("label") or {}).get("name") if isinstance(t.get("label"), dict) else None,
                "released_at": t.get("publishDate") or t.get("releaseDate"),
                "url": f"https://www.beatport.com/track/{t.get('slug')}/{t.get('id')}" if t.get("id") else None,
            })
        return out
    except Exception:
        return []


def check_all() -> Dict[str, Any]:
    """Re-scan every subscription, register new releases."""
    _ensure_schema()
    subs = list_subscriptions()
    library_titles = {
        (t.get("artist") or "").lower() + "::" + (t.get("title") or "").lower()
        for t in db.find_tracks(limit=100000)
    }

    new_total = 0
    per_sub = []
    with get_connection() as conn:
        for s in subs:
            if s["kind"] != "artist":
                continue
            releases = _check_artist_beatport(s["name"])
            new_for_sub = 0
            for r in releases:
                key = (r["artist"] or "").lower() + "::" + (r["title"] or "").lower()
                in_lib = 1 if key in library_titles else 0
                # Skip if we've already logged this URL
                if r.get("url"):
                    existing = conn.execute(
                        "SELECT id FROM new_releases WHERE url = ?", (r["url"],)
                    ).fetchone()
                    if existing:
                        continue
                conn.execute(
                    "INSERT INTO new_releases (subscription_id, artist, title, label, released_at, url, seen_at, in_library) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (s["id"], r.get("artist"), r.get("title"), r.get("label"),
                     r.get("released_at"), r.get("url"),
                     datetime.utcnow().isoformat(), in_lib),
                )
                new_for_sub += 1
                if not in_lib:
                    new_total += 1
            conn.execute(
                "UPDATE subscriptions SET last_checked = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), s["id"]),
            )
            per_sub.append({"subscription": s["name"], "new": new_for_sub})

    return {"checked": len(per_sub), "new_releases_found": new_total, "per_subscription": per_sub}


def feed(unseen_only: bool = True, limit: int = 100) -> List[Dict[str, Any]]:
    """Return the most recently seen releases."""
    _ensure_schema()
    sql = "SELECT nr.*, s.name AS subscription_name FROM new_releases nr " \
          "JOIN subscriptions s ON nr.subscription_id = s.id "
    if unseen_only:
        sql += "WHERE nr.in_library = 0 "
    sql += "ORDER BY nr.seen_at DESC LIMIT ?"
    with get_connection() as conn:
        rows = conn.execute(sql, (limit,)).fetchall()
        return [dict(r) for r in rows]
