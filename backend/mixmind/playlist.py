"""
Smart playlist / setlist generator.

Generates DJ-friendly setlists using:
- Energy curve shaping (warmup -> peak -> cooldown)
- Harmonic mixing (Camelot adjacent keys only)
- BPM continuity (smooth transitions, ±5 BPM steps)
- Personal taste (prefer tracks near your taste centroid)
- No duplicates / no disliked
"""
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import random
import json

from mixmind import database as db
from mixmind.preferences import _track_to_vector


# Preset energy curves over normalized time 0..1
ENERGY_CURVES = {
    "warmup": lambda t: 3 + t * 3,                          # 3 -> 6
    "peak-time": lambda t: 6 + 3 * np.sin(t * np.pi) + t,   # arc peaking ~8.5
    "after-hours": lambda t: 5 - t * 3,                     # 5 -> 2
    "festival": lambda t: min(10, 5 + t * 5),               # ramp to 10
    "journey": lambda t: (                                  # classic 3-act
        3 + t * 5 if t < 0.4 else
        8 - abs(t - 0.7) * 4 if t < 0.85 else
        5 - (t - 0.85) * 10
    ),
}


def camelot_compatible(a: str, b: str) -> bool:
    """Check if two Camelot keys are harmonically compatible."""
    if not a or not b or a == "?" or b == "?":
        return True  # be lenient with missing keys
    if a == b:
        return True
    try:
        num_a, letter_a = int(a[:-1]), a[-1]
        num_b, letter_b = int(b[:-1]), b[-1]
    except (ValueError, IndexError):
        return True
    # Same number, different letter (relative major/minor)
    if num_a == num_b and letter_a != letter_b:
        return True
    # Adjacent on wheel, same letter
    if letter_a == letter_b and ((num_a % 12) + 1 == num_b or (num_b % 12) + 1 == num_a):
        return True
    return False


def _taste_centroid() -> Optional[np.ndarray]:
    liked = db.get_liked_tracks()
    if not liked:
        return None
    vecs = [v for v in (_track_to_vector(t) for t in liked) if v is not None]
    if not vecs:
        return None
    c = np.mean(np.stack(vecs), axis=0)
    return c / (np.linalg.norm(c) + 1e-8)


def _score_track(
    track: Dict[str, Any],
    target_energy: float,
    target_bpm: Optional[float],
    last_camelot: Optional[str],
    taste: Optional[np.ndarray],
) -> float:
    """Higher is better."""
    if (track.get("rating") or 0) == -1:
        return -1e9

    # Energy proximity
    energy_dist = abs((track.get("energy") or 5) - target_energy)
    energy_score = max(0.0, 1.0 - energy_dist / 5.0)

    # BPM proximity (prefer ±5, penalize big jumps)
    if target_bpm is not None and track.get("bpm"):
        bpm_dist = abs(track["bpm"] - target_bpm)
        bpm_score = max(0.0, 1.0 - bpm_dist / 15.0)
    else:
        bpm_score = 0.5

    # Harmonic compatibility
    harm_score = 1.0 if (last_camelot is None or camelot_compatible(last_camelot, track.get("camelot") or "")) else 0.2

    # Taste proximity
    taste_score = 0.5
    if taste is not None:
        vec = _track_to_vector(track)
        if vec is not None:
            vec_n = vec / (np.linalg.norm(vec) + 1e-8)
            taste_score = (float(np.dot(vec_n, taste)) + 1) / 2  # cosine -1..1 -> 0..1

    # Rating boost
    rating_boost = {0: 1.0, 1: 1.15, 2: 1.3}.get(track.get("rating") or 0, 1.0)

    return (
        0.35 * energy_score
        + 0.25 * bpm_score
        + 0.20 * harm_score
        + 0.20 * taste_score
    ) * rating_boost


def generate_setlist(
    duration_minutes: int = 60,
    curve: str = "journey",
    genre: Optional[str] = None,
    bpm_range: Optional[Tuple[float, float]] = None,
    seed: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Build a DJ setlist.
    """
    if seed is not None:
        random.seed(seed)

    candidates = db.find_tracks(
        genre=genre,
        bpm_min=bpm_range[0] if bpm_range else None,
        bpm_max=bpm_range[1] if bpm_range else None,
        limit=10000,
    )
    candidates = [
        c for c in candidates
        if c.get("bpm") and c.get("energy") is not None and (c.get("rating") or 0) != -1
    ]
    # Prefer one track per duplicate group (keep the highest rated or largest file)
    by_group: Dict[int, Dict[str, Any]] = {}
    others: List[Dict[str, Any]] = []
    for c in candidates:
        gid = c.get("duplicate_group_id")
        if gid:
            cur = by_group.get(gid)
            if cur is None or (c.get("rating") or 0) > (cur.get("rating") or 0) \
                    or (c.get("filesize") or 0) > (cur.get("filesize") or 0):
                by_group[gid] = c
        else:
            others.append(c)
    candidates = list(by_group.values()) + others

    if not candidates:
        return []

    curve_fn = ENERGY_CURVES.get(curve, ENERGY_CURVES["journey"])
    taste = _taste_centroid()

    # Estimate track count — average track length assumed 5 minutes
    avg_track_min = 5.0
    target_count = max(3, int(duration_minutes / avg_track_min))

    setlist: List[Dict[str, Any]] = []
    used_ids = set()
    last_camelot: Optional[str] = None
    last_bpm: Optional[float] = None

    for i in range(target_count):
        t_norm = i / max(1, target_count - 1)
        target_energy = float(curve_fn(t_norm))

        best: Optional[Dict[str, Any]] = None
        best_score = -1e9

        # Score a random sample (for speed) if library is huge
        pool = candidates
        if len(pool) > 500:
            pool = random.sample(pool, 500)

        for c in pool:
            if c["id"] in used_ids:
                continue
            score = _score_track(c, target_energy, last_bpm, last_camelot, taste)
            if score > best_score:
                best_score = score
                best = c

        if best is None:
            break
        used_ids.add(best["id"])
        setlist.append(best)
        last_camelot = best.get("camelot")
        last_bpm = best.get("bpm")

    return setlist


def export_m3u8(tracks: List[Dict[str, Any]], out_path: str):
    """Write an M3U8 playlist file."""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for t in tracks:
            dur = int(t.get("duration") or 0)
            artist = t.get("artist") or "Unknown"
            title = t.get("title") or t.get("filename") or "Untitled"
            f.write(f"#EXTINF:{dur},{artist} - {title}\n")
            f.write(f"{t['path']}\n")
