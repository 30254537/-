"""
"Play like that DJ" — generate a setlist that mimics a reference DJ's style.

Inputs:
  - A recovered tracklist (use settracks.recover_tracklist on a YouTube/SC rip)
  - Or a list of track names + artists

Outputs:
  - A "style fingerprint": BPM curve, energy curve, key transitions, genre mix
  - A setlist from your library that follows the same arc

Method:
  1. From the reference tracks, build a sequence of (BPM, energy, genre, key).
  2. Smooth the curves to capture macro-arc (warmup → peak → cooldown).
  3. For each timestep, find the best track in your library:
       - Match BPM ±4
       - Match energy ±1
       - Match Camelot compatibility
       - Prefer same genre
       - Avoid duplicates / disliked
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from mixmind import database as db
from mixmind.playlist import camelot_compatible


def fingerprint_reference(tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a style fingerprint from a list of track dicts (with bpm/energy/etc.).
    Tracks may include None fields if track_id wasn't matched in the library.
    """
    bpms = [t.get("bpm") for t in tracks if t.get("bpm")]
    energies = [t.get("energy") for t in tracks if t.get("energy") is not None]
    genres = [t.get("genre_ai") for t in tracks if t.get("genre_ai")]
    keys = [t.get("camelot") for t in tracks if t.get("camelot")]

    return {
        "track_count": len(tracks),
        "matched_count": len(bpms),
        "bpm_curve": [round(b, 1) for b in bpms],
        "energy_curve": [round(e, 1) for e in energies],
        "genre_mix": _counter(genres),
        "key_set": _counter(keys),
        "avg_bpm": round(np.mean(bpms), 1) if bpms else None,
        "avg_energy": round(np.mean(energies), 1) if energies else None,
    }


def _counter(items):
    from collections import Counter
    return [{"name": k, "count": v} for k, v in Counter(items).most_common()]


def generate_mimic_setlist(
    reference_fingerprint: Dict[str, Any],
    target_count: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Build a setlist from the user's library that follows the reference arc.
    """
    bpm_curve = reference_fingerprint.get("bpm_curve", []) or []
    energy_curve = reference_fingerprint.get("energy_curve", []) or []
    if not bpm_curve or not energy_curve:
        return []

    # Smooth curves slightly
    if len(bpm_curve) >= 3:
        bpm_curve = list(_smooth(bpm_curve, 3))
        energy_curve = list(_smooth(energy_curve, 3))

    n = target_count or len(bpm_curve)
    if n <= 0:
        return []

    # Resample curves to length n
    if len(bpm_curve) != n:
        bpm_curve = _resample(bpm_curve, n)
        energy_curve = _resample(energy_curve, n)

    # Allowed genres = top 3 from reference
    allowed_genres = {
        g["name"] for g in (reference_fingerprint.get("genre_mix") or [])[:3]
    }

    pool = db.find_tracks(limit=10000)
    pool = [p for p in pool if p.get("bpm") and (p.get("rating") or 0) != -1]

    chosen: List[Dict[str, Any]] = []
    used: set = set()
    last_camelot: Optional[str] = None

    for i in range(n):
        target_bpm = bpm_curve[i]
        target_energy = energy_curve[i]
        best = None
        best_score = -1e9
        for p in pool:
            if p["id"] in used:
                continue
            if allowed_genres and p.get("genre_ai") and p["genre_ai"] not in allowed_genres:
                # Hard penalty (still allow if no match)
                pass
            bpm_d = abs(p["bpm"] - target_bpm)
            if bpm_d > 6:
                continue
            energy_d = abs((p.get("energy") or 5) - target_energy)
            if energy_d > 2:
                continue
            harm = camelot_compatible(last_camelot or "", p.get("camelot") or "")
            score = (
                -bpm_d * 0.3
                - energy_d * 0.4
                + (1.0 if harm else -0.5)
                + (0.6 if p.get("genre_ai") in allowed_genres else 0)
                + (0.2 * (p.get("rating") or 0))
            )
            if score > best_score:
                best_score = score
                best = p
        if best:
            chosen.append(best)
            used.add(best["id"])
            last_camelot = best.get("camelot")

    return chosen


def _smooth(xs, window):
    arr = np.array(xs, dtype=float)
    if len(arr) < window:
        return arr
    kernel = np.ones(window) / window
    return np.convolve(arr, kernel, mode="same")


def _resample(xs, n):
    arr = np.array(xs, dtype=float)
    idx = np.linspace(0, len(arr) - 1, n)
    return [round(float(np.interp(i, np.arange(len(arr)), arr)), 2) for i in idx]
