"""
Live Mix Assistant — recommend the next track in real time.

Given the currently-playing track (Deck A) plus optional context like
current play position, picks 3 candidates for Deck B that:

  1. Are harmonically compatible (Camelot adjacency rules)
  2. Have a BPM within ±6% (DJM-class pitch range without artifacts)
  3. Match the current energy curve (steady/build/release modes)
  4. Are taste-compatible (cosine similarity to the user's centroid)
  5. Avoid recently-played tracks (anti-repetition window)

Each candidate is returned with a `mix_score` (0..1), reasons (tags), and
recommended `mix_in_at` / `mix_out_at` time markers that align with
detected phrase boundaries.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional

import numpy as np

from mixmind import database as db
from mixmind.preferences import _track_to_vector
from mixmind.playlist import camelot_compatible


# Sliding window of recently-played track ids (in-process)
_RECENT_PLAYED: List[int] = []
_RECENT_MAX = 30


def mark_played(track_id: int):
    if track_id in _RECENT_PLAYED:
        _RECENT_PLAYED.remove(track_id)
    _RECENT_PLAYED.append(track_id)
    while len(_RECENT_PLAYED) > _RECENT_MAX:
        _RECENT_PLAYED.pop(0)


@dataclass
class MixCandidate:
    track: Dict[str, Any]
    mix_score: float                # 0..1
    bpm_delta: float                # candidate.bpm - current.bpm
    bpm_pct_change: float           # delta / current.bpm  (DJ pitch knob units)
    harmonic: bool                  # True if Camelot compatible
    energy_delta: float
    taste_similarity: float
    reasons: List[str] = field(default_factory=list)
    mix_in_at: Optional[float] = None      # sec into candidate
    mix_out_at: Optional[float] = None     # sec into current track


def _find_phrase_boundaries(beat_times: List[float]) -> List[float]:
    """Phrases ~ 32 bars in 4/4 = 32*4 = 128 beats. Also tag every 8/16."""
    if not beat_times or len(beat_times) < 16:
        return []
    bounds = []
    for i in range(0, len(beat_times), 32):  # every 8 bars
        if i < len(beat_times):
            bounds.append(beat_times[i])
    return bounds


def _taste_centroid() -> Optional[np.ndarray]:
    liked = db.get_liked_tracks()
    if not liked:
        return None
    vecs = [v for v in (_track_to_vector(t) for t in liked) if v is not None]
    if not vecs:
        return None
    c = np.mean(np.stack(vecs), axis=0)
    return c / (np.linalg.norm(c) + 1e-8)


def _score_candidate(
    cand: Dict[str, Any],
    cur: Dict[str, Any],
    taste: Optional[np.ndarray],
    mode: str,
) -> Optional[MixCandidate]:
    if not cand.get("bpm") or not cur.get("bpm"):
        return None
    cur_bpm = float(cur["bpm"])
    cand_bpm = float(cand["bpm"])

    bpm_delta = cand_bpm - cur_bpm
    pct = bpm_delta / cur_bpm
    # Hard reject anything beyond ±8%
    if abs(pct) > 0.08:
        return None

    # Harmonic
    harmonic = camelot_compatible(cur.get("camelot") or "", cand.get("camelot") or "")

    # Energy mode
    cur_e = cur.get("energy") or 5
    cand_e = cand.get("energy") or 5
    energy_delta = cand_e - cur_e

    if mode == "build":
        energy_target = 1.5      # candidate should be ~1.5 hotter
    elif mode == "release":
        energy_target = -1.5
    else:
        energy_target = 0
    energy_score = max(0.0, 1.0 - abs(energy_delta - energy_target) / 4.0)

    # BPM sub-score: smaller change = better (0% perfect)
    bpm_score = max(0.0, 1.0 - abs(pct) / 0.06)

    harm_score = 1.0 if harmonic else 0.25

    taste_sim = 0.5
    if taste is not None:
        v = _track_to_vector(cand)
        if v is not None:
            v_n = v / (np.linalg.norm(v) + 1e-8)
            taste_sim = (float(np.dot(v_n, taste)) + 1) / 2

    rating_boost = {0: 1.0, 1: 1.15, 2: 1.3}.get(cand.get("rating") or 0, 1.0)
    if (cand.get("rating") or 0) == -1:
        return None

    mix_score = (
        0.30 * bpm_score
        + 0.30 * harm_score
        + 0.20 * energy_score
        + 0.20 * taste_sim
    ) * rating_boost
    mix_score = float(min(1.0, mix_score))

    # Build reason tags for UI
    reasons: List[str] = []
    if abs(pct) < 0.005:
        reasons.append("perfect_bpm")
    elif abs(pct) < 0.02:
        reasons.append("close_bpm")
    if harmonic:
        if cur.get("camelot") == cand.get("camelot"):
            reasons.append("same_key")
        else:
            reasons.append("harmonic")
    if mode == "build" and energy_delta > 0.5:
        reasons.append("energy_lift")
    if mode == "release" and energy_delta < -0.5:
        reasons.append("energy_drop")
    if abs(energy_delta) < 0.5 and mode == "steady":
        reasons.append("smooth_continuation")
    if cand.get("genre_ai") == cur.get("genre_ai"):
        reasons.append("same_genre")
    if (cand.get("rating") or 0) >= 1:
        reasons.append("you_like_this")
    if taste_sim > 0.85:
        reasons.append("taste_match")

    # Suggested mix points: outro of current, intro of candidate, snapped to phrases.
    mix_out = cur.get("outro_start") or cur.get("breakdown")
    mix_in = cand.get("intro_end") or 0.0

    # Snap to nearest phrase boundary if available
    cur_beats_json = cur.get("beat_times")
    if cur_beats_json and mix_out:
        try:
            beats = json.loads(cur_beats_json) if isinstance(cur_beats_json, str) else cur_beats_json
            phrases = _find_phrase_boundaries(beats)
            if phrases:
                mix_out = min(phrases, key=lambda p: abs(p - mix_out))
        except Exception:
            pass

    return MixCandidate(
        track=cand,
        mix_score=round(mix_score, 4),
        bpm_delta=round(bpm_delta, 2),
        bpm_pct_change=round(pct * 100, 2),
        harmonic=harmonic,
        energy_delta=round(energy_delta, 2),
        taste_similarity=round(taste_sim, 4),
        reasons=reasons,
        mix_in_at=round(float(mix_in), 2) if mix_in else None,
        mix_out_at=round(float(mix_out), 2) if mix_out else None,
    )


def suggest_next(
    current_track_id: int,
    mode: str = "steady",
    limit: int = 3,
    bpm_window: float = 0.06,
) -> List[Dict[str, Any]]:
    """
    Suggest the top-K next tracks given what's playing on Deck A.
    Modes: steady, build, release.
    """
    cur = db.get_track(current_track_id)
    if not cur:
        return []

    mark_played(current_track_id)
    taste = _taste_centroid()

    cand_pool = db.find_tracks(
        bpm_min=cur["bpm"] * (1 - bpm_window) if cur.get("bpm") else None,
        bpm_max=cur["bpm"] * (1 + bpm_window) if cur.get("bpm") else None,
        limit=2000,
    )

    candidates: List[MixCandidate] = []
    for c in cand_pool:
        if c["id"] == current_track_id or c["id"] in _RECENT_PLAYED:
            continue
        sc = _score_candidate(c, cur, taste, mode)
        if sc is not None:
            candidates.append(sc)

    candidates.sort(key=lambda x: x.mix_score, reverse=True)
    return [asdict(c) for c in candidates[:limit]]
