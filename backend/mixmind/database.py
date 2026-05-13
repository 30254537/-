"""SQLite database layer for the music library."""
import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from datetime import datetime

from mixmind.config import DB_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    filename TEXT NOT NULL,
    filesize INTEGER,
    duration REAL,

    -- Metadata
    title TEXT,
    artist TEXT,
    album TEXT,
    genre_tag TEXT,              -- from file ID3 tag
    year INTEGER,

    -- Audio analysis (professional-grade, real DSP metrics)
    bpm REAL,
    bpm_confidence REAL,         -- 0-1, confidence of BPM detection
    key_name TEXT,               -- e.g. "Am", "C"
    camelot TEXT,                -- e.g. "8A", "8B"
    key_confidence REAL,         -- 0-1, confidence of key detection
    energy REAL,                 -- 0-10 composite
    loudness REAL,               -- integrated LUFS (ITU-R BS.1770-4)
    true_peak REAL,              -- dBFS peak sample
    danceability REAL,           -- 0-1
    brightness REAL,             -- 0-1 (spectral centroid normalized)

    -- Beatgrid + structure (from DSP analysis, suitable for Rekordbox export)
    beat_times TEXT,             -- JSON array of beat times (sec)
    downbeats TEXT,              -- JSON array of downbeat times (sec)
    intro_end REAL,              -- structural cue: end of intro (sec)
    first_drop REAL,             -- first drop / peak energy moment (sec)
    breakdown REAL,              -- breakdown section start (sec)
    outro_start REAL,            -- start of outro (sec)
    waveform_bands TEXT,         -- JSON: low/mid/high RMS envelope for UI

    -- AI classification
    genre_ai TEXT,               -- AI-detected genre
    mood_label TEXT,             -- chill/warmup/groove/peak/intense
    feature_vector TEXT,         -- JSON array for similarity search

    -- User feedback
    rating INTEGER DEFAULT 0,    -- -1 dislike, 0 neutral, 1 like, 2 love
    play_count INTEGER DEFAULT 0,
    last_played TEXT,

    -- Duplicate detection
    audio_fingerprint TEXT,      -- short hash of audio features
    duplicate_group_id INTEGER,  -- tracks in the same group are duplicates

    -- Housekeeping
    scanned_at TEXT NOT NULL,
    analyzed_at TEXT,

    -- Preview
    peak_start REAL,             -- seconds where the hook/drop is
    peak_end REAL
);

CREATE INDEX IF NOT EXISTS idx_tracks_bpm ON tracks(bpm);
CREATE INDEX IF NOT EXISTS idx_tracks_camelot ON tracks(camelot);
CREATE INDEX IF NOT EXISTS idx_tracks_energy ON tracks(energy);
CREATE INDEX IF NOT EXISTS idx_tracks_genre_ai ON tracks(genre_ai);
CREATE INDEX IF NOT EXISTS idx_tracks_rating ON tracks(rating);
CREATE INDEX IF NOT EXISTS idx_tracks_fingerprint ON tracks(audio_fingerprint);

CREATE TABLE IF NOT EXISTS playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS playlist_tracks (
    playlist_id INTEGER NOT NULL,
    track_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    PRIMARY KEY (playlist_id, track_id),
    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scan_folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    last_scanned TEXT
);
"""


@contextmanager
def get_connection():
    """Context manager for DB connections."""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize the database schema."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        # Migrate older DBs: add any missing columns
        existing = {row["name"] for row in conn.execute("PRAGMA table_info(tracks)").fetchall()}
        migrations = [
            ("bpm_confidence", "REAL"),
            ("key_confidence", "REAL"),
            ("true_peak", "REAL"),
            ("beat_times", "TEXT"),
            ("downbeats", "TEXT"),
            ("intro_end", "REAL"),
            ("first_drop", "REAL"),
            ("breakdown", "REAL"),
            ("outro_start", "REAL"),
            ("waveform_bands", "TEXT"),
            ("hot_cues", "TEXT"),                # JSON array of {slot,name,time_sec,color,type}
            ("quality_verdict", "TEXT"),         # quality audit: pristine/lossy_320/fake_320/etc
            ("quality_score", "REAL"),
            ("spectral_cutoff_hz", "REAL"),
            # v0.5 additions
            ("vibe_mood", "TEXT"),               # dark / euphoric / melancholic / uplifting / neutral
            ("vibe_texture", "TEXT"),            # driving / groovy / hypnotic / ethereal / funky
            ("vibe_time", "TEXT"),               # sunset / late_night / sunrise / daytime / anytime
            ("vibe_element", "TEXT"),            # vocal / instrumental / acid / classic / modern
            ("cover_path", "TEXT"),              # local jpg path (extracted/fetched)
            ("sample_type", "TEXT"),             # acapella/drum_loop/fx_riser/etc. (None for full songs)
            # v0.6 — vocal identification
            ("vocal_presence", "REAL"),          # 0..1, fraction of frames with detected vocal
            ("vocal_gender", "TEXT"),            # male / female / mixed / none
            ("vocal_f0_hz", "REAL"),             # median fundamental in vocal frames
            ("vocal_confidence", "REAL"),        # 0..1
            ("vocal_f0_lo", "REAL"),             # 25th percentile pitch
            ("vocal_f0_hi", "REAL"),             # 75th percentile pitch
        ]
        for col, typ in migrations:
            if col not in existing:
                try:
                    conn.execute(f"ALTER TABLE tracks ADD COLUMN {col} {typ}")
                except Exception:
                    pass


def upsert_track(data: Dict[str, Any]) -> int:
    """Insert or update a track by path. Returns track id."""
    with get_connection() as conn:
        cur = conn.cursor()
        # Check if exists
        cur.execute("SELECT id FROM tracks WHERE path = ?", (data["path"],))
        row = cur.fetchone()

        data.setdefault("scanned_at", datetime.utcnow().isoformat())

        if row:
            track_id = row["id"]
            keys = [k for k in data.keys() if k != "path"]
            if keys:
                sets = ", ".join(f"{k} = ?" for k in keys)
                values = [data[k] for k in keys] + [data["path"]]
                cur.execute(f"UPDATE tracks SET {sets} WHERE path = ?", values)
            return track_id
        else:
            cols = list(data.keys())
            placeholders = ", ".join("?" for _ in cols)
            cur.execute(
                f"INSERT INTO tracks ({', '.join(cols)}) VALUES ({placeholders})",
                [data[k] for k in cols],
            )
            return cur.lastrowid


def update_track(track_id: int, data: Dict[str, Any]):
    """Update specific fields of a track."""
    if not data:
        return
    with get_connection() as conn:
        sets = ", ".join(f"{k} = ?" for k in data.keys())
        values = list(data.values()) + [track_id]
        conn.execute(f"UPDATE tracks SET {sets} WHERE id = ?", values)


def get_track(track_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM tracks WHERE id = ?", (track_id,)).fetchone()
        return dict(row) if row else None


def get_track_by_path(path: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM tracks WHERE path = ?", (path,)).fetchone()
        return dict(row) if row else None


def find_tracks(
    query: Optional[str] = None,
    genre: Optional[str] = None,
    mood: Optional[str] = None,
    bpm_min: Optional[float] = None,
    bpm_max: Optional[float] = None,
    camelot: Optional[str] = None,
    rating: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    sql = "SELECT * FROM tracks WHERE 1=1"
    params: list = []
    if query:
        sql += " AND (title LIKE ? OR artist LIKE ? OR filename LIKE ?)"
        q = f"%{query}%"
        params.extend([q, q, q])
    if genre:
        sql += " AND (genre_ai = ? OR genre_tag LIKE ?)"
        params.extend([genre, f"%{genre}%"])
    if mood:
        sql += " AND mood_label = ?"
        params.append(mood)
    if bpm_min is not None:
        sql += " AND bpm >= ?"
        params.append(bpm_min)
    if bpm_max is not None:
        sql += " AND bpm <= ?"
        params.append(bpm_max)
    if camelot:
        sql += " AND camelot = ?"
        params.append(camelot)
    if rating is not None:
        sql += " AND rating = ?"
        params.append(rating)
    sql += " ORDER BY artist, title LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def count_tracks() -> int:
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]


def get_stats() -> Dict[str, Any]:
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
        analyzed = conn.execute(
            "SELECT COUNT(*) FROM tracks WHERE bpm IS NOT NULL"
        ).fetchone()[0]
        liked = conn.execute(
            "SELECT COUNT(*) FROM tracks WHERE rating >= 1"
        ).fetchone()[0]
        disliked = conn.execute(
            "SELECT COUNT(*) FROM tracks WHERE rating = -1"
        ).fetchone()[0]
        duplicates = conn.execute(
            "SELECT COUNT(*) FROM tracks WHERE duplicate_group_id IS NOT NULL"
        ).fetchone()[0]
        genres = conn.execute(
            "SELECT genre_ai, COUNT(*) as c FROM tracks "
            "WHERE genre_ai IS NOT NULL GROUP BY genre_ai ORDER BY c DESC"
        ).fetchall()
        moods = conn.execute(
            "SELECT mood_label, COUNT(*) as c FROM tracks "
            "WHERE mood_label IS NOT NULL GROUP BY mood_label ORDER BY c DESC"
        ).fetchall()
        total_duration = conn.execute(
            "SELECT SUM(duration) FROM tracks"
        ).fetchone()[0] or 0
    return {
        "total_tracks": total,
        "analyzed": analyzed,
        "liked": liked,
        "disliked": disliked,
        "duplicates": duplicates,
        "total_hours": round(total_duration / 3600, 1),
        "genres": [dict(g) for g in genres],
        "moods": [dict(m) for m in moods],
    }


def set_rating(track_id: int, rating: int):
    with get_connection() as conn:
        conn.execute("UPDATE tracks SET rating = ? WHERE id = ?", (rating, track_id))


def get_liked_tracks() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM tracks WHERE rating >= 1 AND feature_vector IS NOT NULL"
        ).fetchall()
        return [dict(r) for r in rows]


def get_analyzed_tracks() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM tracks WHERE feature_vector IS NOT NULL"
        ).fetchall()
        return [dict(r) for r in rows]


def save_playlist(name: str, track_ids: List[int], description: str = "") -> int:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO playlists (name, description, created_at) VALUES (?, ?, ?)",
            (name, description, datetime.utcnow().isoformat()),
        )
        pid = cur.lastrowid
        cur.execute("DELETE FROM playlist_tracks WHERE playlist_id = ?", (pid,))
        for i, tid in enumerate(track_ids):
            cur.execute(
                "INSERT INTO playlist_tracks (playlist_id, track_id, position) VALUES (?, ?, ?)",
                (pid, tid, i),
            )
        return pid


def get_playlists() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT p.*, COUNT(pt.track_id) as track_count "
            "FROM playlists p LEFT JOIN playlist_tracks pt ON p.id = pt.playlist_id "
            "GROUP BY p.id ORDER BY p.created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_playlist_tracks(playlist_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT t.* FROM tracks t "
            "JOIN playlist_tracks pt ON t.id = pt.track_id "
            "WHERE pt.playlist_id = ? "
            "ORDER BY pt.position",
            (playlist_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def find_duplicate_groups() -> List[List[Dict[str, Any]]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM tracks WHERE duplicate_group_id IS NOT NULL "
            "ORDER BY duplicate_group_id, filesize DESC"
        ).fetchall()
        groups: Dict[int, List[Dict[str, Any]]] = {}
        for r in rows:
            d = dict(r)
            groups.setdefault(d["duplicate_group_id"], []).append(d)
        return list(groups.values())
