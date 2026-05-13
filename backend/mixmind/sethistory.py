"""
Set History — long-term DJ style analytics.

Records every set you've recovered (via settracks.py) and aggregates:

  - Total sets played
  - Total hours mixed
  - Unique tracks vs total plays  (re-use rate)
  - Most-played top 10 / 50 tracks
  - BPM histogram (when you actually peak vs cool down)
  - Camelot histogram (favorite keys)
  - Genre distribution
  - Style drift over time (3-month windows)
  - Per-venue style profiles
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional

from mixmind.database import get_connection


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def _ensure_schema():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                played_at TEXT NOT NULL,
                venue TEXT,
                duration_sec REAL,
                source_file TEXT,
                notes TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS set_plays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                set_id INTEGER NOT NULL,
                track_id INTEGER,
                position INTEGER,
                start_sec REAL,
                end_sec REAL,
                confidence REAL,
                FOREIGN KEY (set_id) REFERENCES sets(id) ON DELETE CASCADE
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_setplays_set ON set_plays(set_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_setplays_track ON set_plays(track_id)")


def record_set(
    name: str,
    tracklist_payload: Dict[str, Any],
    venue: Optional[str] = None,
    notes: Optional[str] = None,
    played_at: Optional[str] = None,
) -> int:
    """Persist a recovered tracklist as a Set in history."""
    _ensure_schema()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sets (name, played_at, venue, duration_sec, source_file, notes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                name,
                played_at or datetime.utcnow().isoformat(),
                venue,
                tracklist_payload.get("duration_sec"),
                tracklist_payload.get("set_path"),
                notes,
            ),
        )
        set_id = cur.lastrowid
        for i, e in enumerate(tracklist_payload.get("entries", [])):
            cur.execute(
                "INSERT INTO set_plays (set_id, track_id, position, start_sec, end_sec, confidence) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (set_id, e.get("track_id"), i, e.get("start_sec"), e.get("end_sec"), e.get("confidence")),
            )
        return set_id


def get_history(limit: int = 100) -> List[Dict[str, Any]]:
    _ensure_schema()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT s.*, COUNT(sp.id) AS track_count "
            "FROM sets s LEFT JOIN set_plays sp ON s.id = sp.set_id "
            "GROUP BY s.id ORDER BY s.played_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_set(set_id: int) -> Optional[Dict[str, Any]]:
    _ensure_schema()
    with get_connection() as conn:
        s = conn.execute("SELECT * FROM sets WHERE id = ?", (set_id,)).fetchone()
        if not s:
            return None
        plays = conn.execute(
            "SELECT sp.*, t.artist, t.title, t.bpm, t.camelot, t.energy, t.genre_ai "
            "FROM set_plays sp LEFT JOIN tracks t ON sp.track_id = t.id "
            "WHERE sp.set_id = ? ORDER BY sp.position",
            (set_id,),
        ).fetchall()
        return {**dict(s), "tracks": [dict(r) for r in plays]}


def style_profile(since_days: Optional[int] = None) -> Dict[str, Any]:
    """Aggregate report across all (or recent) sets."""
    _ensure_schema()
    with get_connection() as conn:
        date_filter = ""
        params: list = []
        if since_days:
            date_filter = " AND s.played_at >= datetime('now', ? )"
            params.append(f"-{since_days} days")

        plays = conn.execute(
            f"SELECT t.id, t.artist, t.title, t.bpm, t.camelot, t.genre_ai, t.energy "
            f"FROM set_plays sp "
            f"JOIN sets s ON sp.set_id = s.id "
            f"LEFT JOIN tracks t ON sp.track_id = t.id "
            f"WHERE sp.track_id IS NOT NULL{date_filter}",
            params,
        ).fetchall()
        plays = [dict(p) for p in plays]

        sets_count = conn.execute(
            f"SELECT COUNT(*) FROM sets s WHERE 1=1{date_filter.replace('s.played_at', 's.played_at')}",
            params,
        ).fetchone()[0]

    total_plays = len(plays)
    unique_tracks = len({p["id"] for p in plays})
    reuse_rate = round(1 - unique_tracks / max(1, total_plays), 3) if total_plays else 0.0

    top_tracks = Counter((p["artist"], p["title"]) for p in plays).most_common(10)
    bpm_hist = Counter(int((p["bpm"] or 120) // 2) * 2 for p in plays)
    camelot_hist = Counter(p["camelot"] for p in plays if p["camelot"])
    genre_hist = Counter(p["genre_ai"] for p in plays if p["genre_ai"])

    return {
        "sets_played": sets_count,
        "total_plays": total_plays,
        "unique_tracks": unique_tracks,
        "reuse_rate": reuse_rate,
        "top_tracks": [
            {"artist": k[0], "title": k[1], "count": v} for k, v in top_tracks
        ],
        "bpm_histogram": [{"bucket": int(b), "count": c} for b, c in sorted(bpm_hist.items())],
        "camelot_histogram": [{"key": k, "count": c} for k, c in camelot_hist.most_common()],
        "genre_histogram": [{"genre": g, "count": c} for g, c in genre_hist.most_common()],
    }


def style_drift() -> Dict[str, Any]:
    """Compare last 90 days vs prior 90 days."""
    recent = style_profile(since_days=90)
    with get_connection() as conn:
        plays = conn.execute(
            "SELECT t.genre_ai, t.bpm, t.energy "
            "FROM set_plays sp "
            "JOIN sets s ON sp.set_id = s.id "
            "LEFT JOIN tracks t ON sp.track_id = t.id "
            "WHERE sp.track_id IS NOT NULL "
            "AND s.played_at < datetime('now', '-90 days') "
            "AND s.played_at >= datetime('now', '-180 days')"
        ).fetchall()
        prior = [dict(p) for p in plays]

    def _avg(rows, key):
        vals = [r[key] for r in rows if r.get(key) is not None]
        return round(sum(vals) / len(vals), 2) if vals else None

    prior_genres = Counter(p["genre_ai"] for p in prior if p["genre_ai"])
    recent_genres_d = {g["genre"]: g["count"] for g in recent["genre_histogram"]}
    prior_genres_d = dict(prior_genres)

    all_genres = set(recent_genres_d) | set(prior_genres_d)
    drift = {
        g: {
            "recent": recent_genres_d.get(g, 0),
            "prior": prior_genres_d.get(g, 0),
            "delta": recent_genres_d.get(g, 0) - prior_genres_d.get(g, 0),
        }
        for g in all_genres
    }

    return {
        "recent_avg_bpm": _avg([{"bpm": x["bucket"]} for x in recent["bpm_histogram"]], "bpm"),
        "prior_avg_bpm": _avg(prior, "bpm"),
        "recent_avg_energy": None,
        "prior_avg_energy": _avg(prior, "energy"),
        "genre_shift": drift,
    }
