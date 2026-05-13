"""
Sample / Loop / Acapella library — separate index for short clips.

Re-uses the same SQLite DB but sets sample_type so you can search for
"127 BPM 8A vocal acapella" in one shot.

sample_type values:
  acapella          — full vocal (from AI Stems output)
  instrumental      — instrumental version (no vocal)
  vocal_chop        — short cut/sliced vocal
  drum_loop         — kick + perc loop
  bass_loop         — bass-only loop
  fx_riser          — riser / build-up FX
  fx_impact         — impact / hit one-shot
  fx_drop           — drop FX
  one_shot_kick     — single kick hit
  one_shot_snare
  one_shot_perc
  ambient_pad       — pad / texture
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from mixmind import database as db
from mixmind.scanner import iter_audio_files, extract_tags


SAMPLE_TYPES = [
    "acapella",
    "instrumental",
    "vocal_chop",
    "drum_loop",
    "bass_loop",
    "fx_riser",
    "fx_impact",
    "fx_drop",
    "one_shot_kick",
    "one_shot_snare",
    "one_shot_perc",
    "ambient_pad",
]


# Heuristic: classify a sample by filename keywords
KEYWORD_RULES: List[tuple] = [
    (("acapella", "acap", "vox only", "vocal only"), "acapella"),
    (("instrumental", "inst", "no vocal"), "instrumental"),
    (("vocal chop", "vox chop", "chop"), "vocal_chop"),
    (("drum loop", "drumloop", "drums loop"), "drum_loop"),
    (("bass loop", "bassloop", "bassline"), "bass_loop"),
    (("riser", "uplift"), "fx_riser"),
    (("impact", "hit", "boom"), "fx_impact"),
    (("drop fx", "drop hit"), "fx_drop"),
    (("kick",), "one_shot_kick"),
    (("snare", "clap"), "one_shot_snare"),
    (("perc", "shaker", "tambourine"), "one_shot_perc"),
    (("pad", "ambient", "drone", "texture"), "ambient_pad"),
]


def _classify_filename(filename: str) -> str:
    f = filename.lower()
    for kws, label in KEYWORD_RULES:
        if any(kw in f for kw in kws):
            return label
    return "vocal_chop" if "vocal" in f else "one_shot_perc"


def _ensure_schema():
    """Add a sample_type column if not present."""
    from mixmind.database import get_connection
    with get_connection() as conn:
        existing = {row["name"] for row in conn.execute("PRAGMA table_info(tracks)").fetchall()}
        if "sample_type" not in existing:
            try:
                conn.execute("ALTER TABLE tracks ADD COLUMN sample_type TEXT")
            except Exception:
                pass


def scan_sample_folder(folder: str) -> Dict[str, Any]:
    """Scan a sample folder, classify each file, and add to library."""
    _ensure_schema()
    files = list(iter_audio_files(folder))
    added = 0
    by_type: Dict[str, int] = {}
    for fp in files:
        try:
            tags = extract_tags(fp)
            stype = _classify_filename(fp.name)
            tags["sample_type"] = stype
            db.upsert_track(tags)
            added += 1
            by_type[stype] = by_type.get(stype, 0) + 1
        except Exception:
            continue
    return {"added": added, "total_files": len(files), "by_type": by_type}


def find_samples(
    sample_type: Optional[str] = None,
    bpm_min: Optional[float] = None,
    bpm_max: Optional[float] = None,
    camelot: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    _ensure_schema()
    from mixmind.database import get_connection
    sql = "SELECT * FROM tracks WHERE sample_type IS NOT NULL"
    params: list = []
    if sample_type:
        sql += " AND sample_type = ?"
        params.append(sample_type)
    if bpm_min:
        sql += " AND bpm >= ?"
        params.append(bpm_min)
    if bpm_max:
        sql += " AND bpm <= ?"
        params.append(bpm_max)
    if camelot:
        sql += " AND camelot = ?"
        params.append(camelot)
    if query:
        sql += " AND (filename LIKE ? OR title LIKE ?)"
        q = f"%{query}%"
        params.extend([q, q])
    sql += " ORDER BY filename LIMIT ?"
    params.append(limit)
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def stems_to_acapellas(stems_jobs_dir: str) -> Dict[str, Any]:
    """
    Given a directory containing AI Stems output, register all `vocals.wav`
    as acapella samples and `other.wav` + drums + bass as instrumental.
    """
    _ensure_schema()
    p = Path(stems_jobs_dir)
    if not p.exists():
        return {"error": f"Not found: {stems_jobs_dir}"}
    added = 0
    for vocals in p.rglob("vocals.wav"):
        try:
            tags = extract_tags(vocals)
            tags["sample_type"] = "acapella"
            db.upsert_track(tags)
            added += 1
        except Exception:
            pass
    return {"acapellas_added": added}
