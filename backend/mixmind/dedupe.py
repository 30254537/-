"""
Duplicate / near-duplicate detection.

Strategy:
1. Group tracks with identical audio_fingerprint (same content).
2. Within remaining, group by normalized (artist, title_stem) — catches
   "Extended Mix", "Radio Edit", "Original Mix" variants of the same song.
"""
import re
from typing import List, Dict, Any, Tuple
from collections import defaultdict

from mixmind import database as db


# Words that indicate a version, not a different track
VERSION_KEYWORDS = [
    "original mix",
    "extended mix",
    "extended",
    "radio edit",
    "radio mix",
    "club mix",
    "club edit",
    "vip mix",
    "vip",
    "instrumental",
    "a cappella",
    "acapella",
    "edit",
    "remix",
    "rework",
    "rerub",
    "bootleg",
    "mashup",
    "dub mix",
    "dub",
    "clean",
    "dirty",
    "explicit",
    "intro",
    "outro",
    "short edit",
    "long version",
    "long mix",
    "mix",
]


def _normalize_title(title: str) -> str:
    """Strip version markers to get a song's base name."""
    if not title:
        return ""
    t = title.lower()
    # Remove bracketed content
    t = re.sub(r"[\[\(\{][^\]\)\}]*[\]\)\}]", " ", t)
    # Remove version keywords
    for kw in sorted(VERSION_KEYWORDS, key=len, reverse=True):
        t = re.sub(rf"\b{re.escape(kw)}\b", " ", t)
    # Remove special chars
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _normalize_artist(artist: str) -> str:
    if not artist:
        return ""
    a = artist.lower()
    a = re.sub(r"\b(feat\.?|ft\.?|featuring|vs\.?|&|and|with)\b.*$", "", a)
    a = re.sub(r"[^\w\s]", " ", a)
    a = re.sub(r"\s+", " ", a).strip()
    return a


def find_duplicates() -> Tuple[int, int]:
    """
    Detect duplicates and write duplicate_group_id to the database.
    Returns (num_groups, num_tracks_in_groups).
    """
    all_tracks = db.get_analyzed_tracks()

    # Clear previous groups
    from mixmind.database import get_connection
    with get_connection() as conn:
        conn.execute("UPDATE tracks SET duplicate_group_id = NULL")

    groups: Dict[str, List[int]] = defaultdict(list)

    # Bucket 1: identical audio fingerprint (true duplicates)
    for t in all_tracks:
        fp = t.get("audio_fingerprint")
        if fp:
            groups[f"fp:{fp}"].append(t["id"])

    # Bucket 2: same artist + normalized title (version variants)
    for t in all_tracks:
        artist = _normalize_artist(t.get("artist") or "")
        title = _normalize_title(t.get("title") or "")
        if artist and title:
            key = f"at:{artist}::{title}"
            groups[key].append(t["id"])

    # Keep only groups with >= 2 tracks
    group_id = 1
    total_tracks = 0
    assigned: Dict[int, int] = {}
    for key, track_ids in groups.items():
        unique_ids = list(set(track_ids))
        if len(unique_ids) < 2:
            continue
        # If any track already assigned, skip (take the first grouping)
        if any(tid in assigned for tid in unique_ids):
            continue
        for tid in unique_ids:
            assigned[tid] = group_id
        group_id += 1
        total_tracks += len(unique_ids)

    with get_connection() as conn:
        for tid, gid in assigned.items():
            conn.execute(
                "UPDATE tracks SET duplicate_group_id = ? WHERE id = ?",
                (gid, tid),
            )

    return group_id - 1, total_tracks
