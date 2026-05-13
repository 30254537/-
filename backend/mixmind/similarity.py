"""
Sound-similarity search beyond Camelot/BPM.

Operates on the 24-dim feature_vector that the analyzer already stored.
Finds tracks that "sound" similar based on:

  - Timbre  (MFCC components)
  - Tonality (chroma)
  - Spectral shape (centroid / rolloff / bandwidth)
  - Rhythm proxies (zcr, flatness)

This complements Camelot/BPM-based search — two tracks can be in totally
different keys yet sound very similar because they share a vibe (warm
analog pads, glassy stabs, deep sub bass, etc.).
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from mixmind import database as db


def _vec(track: Dict[str, Any]) -> Optional[np.ndarray]:
    fv = track.get("feature_vector")
    if not fv:
        return None
    try:
        v = json.loads(fv) if isinstance(fv, str) else fv
        return np.array(v, dtype=np.float32)
    except Exception:
        return None


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a) + 1e-8
    nb = np.linalg.norm(b) + 1e-8
    return float(np.dot(a, b) / (na * nb))


def find_sonic_neighbors(
    track_id: int,
    limit: int = 30,
    same_genre_only: bool = False,
    bpm_window: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Find tracks that sound like `track_id` in a deeper sense than Camelot/BPM.

    bpm_window: if set, only consider tracks within ±bpm_window BPM
    same_genre_only: if True, filter to same genre_ai
    """
    target = db.get_track(track_id)
    if not target:
        return []
    tv = _vec(target)
    if tv is None:
        return []

    candidates = db.get_analyzed_tracks()
    scored: List[Tuple[float, Dict[str, Any]]] = []
    for c in candidates:
        if c["id"] == track_id:
            continue
        if same_genre_only and c.get("genre_ai") != target.get("genre_ai"):
            continue
        if bpm_window and target.get("bpm") and c.get("bpm"):
            if abs(c["bpm"] - target["bpm"]) > bpm_window:
                continue
        cv = _vec(c)
        if cv is None or len(cv) != len(tv):
            continue
        sim = _cosine(tv, cv)
        scored.append((sim, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    for sim, t in scored[:limit]:
        d = dict(t)
        d["similarity_score"] = round(sim, 4)
        # Also report what's similar/different to the target
        d["bpm_delta"] = (
            round(t["bpm"] - target["bpm"], 2) if t.get("bpm") and target.get("bpm") else None
        )
        d["energy_delta"] = (
            round(t["energy"] - target["energy"], 2) if t.get("energy") is not None and target.get("energy") is not None else None
        )
        d["same_camelot"] = t.get("camelot") == target.get("camelot")
        out.append(d)
    return out
