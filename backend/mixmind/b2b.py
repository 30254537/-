"""
B2B compatibility — find common ground between two DJs' libraries.

Two ways to use it:
  1. Two MixMind databases (yours + a friend's exported library)
  2. Two playlists in the same DB (e.g., "My set" vs "Their set")

Computes:
  - Overlap (tracks both have)
  - Shared BPM zones (where both have ample inventory)
  - Shared key affinities
  - Recommended common-ground setlist that both can play comfortably
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from mixmind import database as db


def overlap_by_fingerprint(other_track_ids: List[int]) -> Dict[str, Any]:
    """
    Given a list of track IDs from another database (or playlist), find which of
    THEIR tracks YOU also have, by fingerprint match.

    Since we can't access the other database here, callers pass the partner's
    fingerprint set directly via `partner_fingerprints`.
    """
    raise NotImplementedError("Use compare_libraries with explicit fingerprint sets")


def compare_libraries(
    your_ids: List[int],
    partner_meta: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compare your library subset (your_ids) against partner_meta — a list of
    dicts with at minimum `audio_fingerprint`, `artist`, `title`, `bpm`, `camelot`.

    Partner data can come from a JSON export of their MixMind database.
    """
    your_tracks = [db.get_track(i) for i in your_ids]
    your_tracks = [t for t in your_tracks if t]
    your_fp = {t.get("audio_fingerprint"): t for t in your_tracks if t.get("audio_fingerprint")}

    common: List[Dict[str, Any]] = []
    only_partner: List[Dict[str, Any]] = []
    for p in partner_meta:
        fp = p.get("audio_fingerprint")
        if fp and fp in your_fp:
            common.append({
                "your_track": your_fp[fp],
                "partner_track": p,
            })
        else:
            only_partner.append(p)

    # BPM histogram intersection
    your_bpm = Counter(int((t["bpm"] or 0) // 2) * 2 for t in your_tracks if t.get("bpm"))
    partner_bpm = Counter(
        int((p.get("bpm") or 0) // 2) * 2 for p in partner_meta if p.get("bpm")
    )
    shared_bpm = {
        bucket: min(your_bpm[bucket], partner_bpm.get(bucket, 0))
        for bucket in your_bpm
        if partner_bpm.get(bucket, 0) > 0
    }

    # Camelot affinity intersection
    your_keys = Counter(t["camelot"] for t in your_tracks if t.get("camelot"))
    partner_keys = Counter(p.get("camelot") for p in partner_meta if p.get("camelot"))
    shared_keys = {
        k: min(your_keys[k], partner_keys.get(k, 0))
        for k in your_keys
        if partner_keys.get(k, 0) > 0
    }

    return {
        "your_track_count": len(your_tracks),
        "partner_track_count": len(partner_meta),
        "common_tracks": common,
        "common_count": len(common),
        "partner_only_count": len(only_partner),
        "shared_bpm_histogram": [
            {"bucket": b, "your": your_bpm[b], "partner": partner_bpm.get(b, 0), "shared": s}
            for b, s in sorted(shared_bpm.items())
        ],
        "shared_keys": [
            {"camelot": k, "your": your_keys[k], "partner": partner_keys.get(k, 0)}
            for k in sorted(shared_keys, key=lambda x: -shared_keys[x])
        ],
    }


def b2b_setlist(
    your_ids: List[int],
    partner_meta: List[Dict[str, Any]],
    duration_minutes: int = 60,
) -> List[Dict[str, Any]]:
    """
    Build a B2B setlist alternating between your tracks and the partner's.
    Each entry is tagged with `dj` ('you' or 'partner') so you know who plays it.
    """
    cmp = compare_libraries(your_ids, partner_meta)

    # Pick BPM zone where both have inventory
    if not cmp["shared_bpm_histogram"]:
        return []
    target_bpm = max(cmp["shared_bpm_histogram"], key=lambda x: x["shared"])["bucket"]

    # Filter pools
    your_tracks = [
        t for t in (db.get_track(i) for i in your_ids)
        if t and t.get("bpm") and abs(t["bpm"] - target_bpm) < 6
    ]
    partner_tracks = [
        p for p in partner_meta
        if p.get("bpm") and abs(p["bpm"] - target_bpm) < 6
    ]

    # ~5 min per track
    n = max(2, duration_minutes // 5)
    out = []
    yi, pi = 0, 0
    last_camelot = None
    from mixmind.playlist import camelot_compatible

    for slot in range(n):
        candidates = your_tracks[yi:] if slot % 2 == 0 else partner_tracks[pi:]
        # Pick first harmonically compatible
        choice = None
        for c in candidates:
            if camelot_compatible(last_camelot or "", c.get("camelot") or ""):
                choice = c
                break
        if not choice and candidates:
            choice = candidates[0]
        if not choice:
            break
        if slot % 2 == 0:
            yi += 1
            out.append({**choice, "dj": "you"})
        else:
            pi += 1
            out.append({**choice, "dj": "partner"})
        last_camelot = choice.get("camelot") or last_camelot
    return out
