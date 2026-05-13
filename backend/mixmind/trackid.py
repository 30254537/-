"""
Track ID — audio fingerprint matching.

Identify unknown tracks (bootlegs, mashups, phone recordings, ripped sets)
using a layered approach:

1. **Local fingerprint match** — Chromaprint-style constant-Q chroma
   landmark hashes. Robust to time-shift, EQ, light pitch shift, noise.
2. **AcoustID online lookup** — if pyacoustid + fpcalc available, query
   the public AcoustID database for MusicBrainz IDs.
3. **Discogs validation** — given artist/title from step 1 or 2, verify
   against Discogs metadata for label / release year / catalog number.

This module ships with the local matcher always active. The online steps
are optional and degrade gracefully when offline or unconfigured.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from mixmind import database as db
from mixmind.config import HOP_LENGTH, SAMPLE_RATE


# ----------------------------------------------------------------------------
# Local fingerprint — landmark hashing of CQT chroma peaks
# ----------------------------------------------------------------------------

@dataclass
class FingerprintMatch:
    track_id: Optional[int]
    title: Optional[str]
    artist: Optional[str]
    album: Optional[str]
    confidence: float           # 0..1
    matched_landmarks: int
    total_landmarks: int
    source: str                 # "local" | "acoustid" | "discogs"
    metadata: Dict[str, Any]


def _librosa():
    import librosa
    return librosa


def _chroma_landmarks(y: np.ndarray, sr: int) -> List[Tuple[int, int]]:
    """
    Generate (time_frame, peak_chroma) landmarks robust to small distortions.
    Each landmark = the dominant chroma bin at that frame.
    """
    librosa = _librosa()
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=HOP_LENGTH)
    # Smooth slightly to suppress single-frame noise
    if chroma.shape[1] > 5:
        chroma = np.apply_along_axis(
            lambda row: np.convolve(row, np.ones(5) / 5, mode="same"), 1, chroma
        )
    peaks = chroma.argmax(axis=0)
    return [(int(t), int(p)) for t, p in enumerate(peaks)]


def compute_landmark_fingerprint(path: str, max_seconds: float = 60.0) -> Dict[str, Any]:
    """
    Build a landmark hash sequence from the first `max_seconds` of audio.

    Returns dict:
      {
        "landmarks": List[Tuple[frame_idx, peak_chroma_bin]],
        "hashes":    List[str]   # 4-frame sliding-window hashes
        "duration":  float
      }
    """
    librosa = _librosa()
    y, sr = librosa.load(path, sr=SAMPLE_RATE, mono=True, duration=max_seconds)
    if len(y) < sr:
        return {"landmarks": [], "hashes": [], "duration": 0.0}

    landmarks = _chroma_landmarks(y, sr)

    # 4-frame sliding-window hash (analogous to Shazam's anchor pairs)
    hashes: List[str] = []
    for i in range(len(landmarks) - 3):
        window = landmarks[i: i + 4]
        # Encode the 4 chroma bins + relative time deltas
        deltas = [window[j + 1][0] - window[j][0] for j in range(3)]
        peaks = [w[1] for w in window]
        payload = ",".join(map(str, peaks + deltas))
        h = hashlib.blake2b(payload.encode(), digest_size=4).hexdigest()
        hashes.append(h)

    return {
        "landmarks": landmarks,
        "hashes": hashes,
        "duration": float(len(y) / sr),
    }


def _hash_overlap(a: List[str], b: List[str]) -> Tuple[int, float]:
    """Count shared hashes (set intersection) and return ratio over min length."""
    if not a or not b:
        return 0, 0.0
    sa, sb = set(a), set(b)
    inter = sa & sb
    base = min(len(sa), len(sb))
    return len(inter), len(inter) / max(1, base)


def match_against_library(query_path: str, top_k: int = 5) -> List[FingerprintMatch]:
    """
    Build a fingerprint of `query_path`, then compare against every analyzed
    track in the library by hash overlap. Returns the top-K matches sorted by
    confidence.
    """
    fp = compute_landmark_fingerprint(query_path)
    qhashes = fp["hashes"]
    if not qhashes:
        return []

    results: List[FingerprintMatch] = []
    for track in db.get_analyzed_tracks():
        # We cache landmark hashes inside feature_vector? No — keep separate.
        ref_path = track.get("path")
        if not ref_path or not os.path.exists(ref_path):
            continue
        try:
            ref_fp = compute_landmark_fingerprint(ref_path, max_seconds=45.0)
        except Exception:
            continue
        n_match, ratio = _hash_overlap(qhashes, ref_fp["hashes"])
        if n_match < 4:
            continue
        confidence = float(np.clip(ratio * 1.5, 0, 1))
        results.append(FingerprintMatch(
            track_id=track["id"],
            title=track.get("title"),
            artist=track.get("artist"),
            album=track.get("album"),
            confidence=round(confidence, 4),
            matched_landmarks=n_match,
            total_landmarks=len(qhashes),
            source="local",
            metadata={
                "bpm": track.get("bpm"),
                "camelot": track.get("camelot"),
                "genre": track.get("genre_ai"),
            },
        ))

    results.sort(key=lambda r: r.confidence, reverse=True)
    return results[:top_k]


# ----------------------------------------------------------------------------
# AcoustID online lookup (optional)
# ----------------------------------------------------------------------------

ACOUSTID_API_KEY = os.environ.get("ACOUSTID_API_KEY", "")


def acoustid_lookup(path: str) -> Optional[Dict[str, Any]]:
    """
    Query AcoustID for MusicBrainz match. Requires:
      - `acoustid` python package
      - `fpcalc` binary (Chromaprint) on PATH
      - ACOUSTID_API_KEY env var
    Returns dict with title/artist/release/score, or None.
    """
    if not ACOUSTID_API_KEY:
        return None
    try:
        import acoustid
    except ImportError:
        return None
    try:
        results = acoustid.match(ACOUSTID_API_KEY, path, parse=True)
    except Exception:
        return None
    for score, recording_id, title, artist in results:
        return {
            "score": float(score),
            "recording_id": recording_id,
            "title": title,
            "artist": artist,
            "source": "acoustid",
        }
    return None


# ----------------------------------------------------------------------------
# Discogs validation (optional)
# ----------------------------------------------------------------------------

DISCOGS_TOKEN = os.environ.get("DISCOGS_TOKEN", "")


def discogs_validate(artist: str, title: str) -> Optional[Dict[str, Any]]:
    """Search Discogs and return the top release match."""
    if not DISCOGS_TOKEN or not artist or not title:
        return None
    try:
        import requests
    except ImportError:
        return None
    try:
        r = requests.get(
            "https://api.discogs.com/database/search",
            params={"artist": artist, "track": title, "type": "release"},
            headers={"Authorization": f"Discogs token={DISCOGS_TOKEN}",
                     "User-Agent": "MixMindDJ/0.4 +https://github.com/mixmind"},
            timeout=8,
        )
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        if not results:
            return None
        top = results[0]
        return {
            "label": top.get("label", [None])[0] if top.get("label") else None,
            "year": top.get("year"),
            "catalog_number": top.get("catno"),
            "country": top.get("country"),
            "release_id": top.get("id"),
            "thumb": top.get("thumb"),
            "source": "discogs",
        }
    except Exception:
        return None


# ----------------------------------------------------------------------------
# Top-level entry point used by API
# ----------------------------------------------------------------------------

def identify_track(path: str) -> Dict[str, Any]:
    """
    Run the full Track ID pipeline against `path`.
    Always returns at least the local-match list, possibly empty.
    """
    local = match_against_library(path, top_k=5)
    online = acoustid_lookup(path)
    enriched = None
    if local:
        top = local[0]
        if top.artist and top.title:
            enriched = discogs_validate(top.artist, top.title)
    elif online:
        enriched = discogs_validate(online.get("artist") or "", online.get("title") or "")

    return {
        "local_matches": [asdict(m) for m in local],
        "online": online,
        "discogs": enriched,
    }
