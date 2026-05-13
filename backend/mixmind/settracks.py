"""
Set Recording → Tracklist Recovery.

Given a long recording (your 2-hour DJ set), slide a window across it
fingerprinting every 30 seconds and matching against your library to
auto-recover the played tracklist.

Output formats:
  - JSON list of {start, end, track, confidence}
  - 1001tracklists.com cue sheet format
  - Plain text "00:00 - 04:32  Artist - Title"
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from mixmind import database as db
from mixmind.config import HOP_LENGTH, SAMPLE_RATE
from mixmind.trackid import _chroma_landmarks


@dataclass
class TracklistEntry:
    start_sec: float
    end_sec: float
    track_id: Optional[int]
    artist: Optional[str]
    title: Optional[str]
    confidence: float


def _librosa():
    import librosa
    return librosa


def _load_library_fingerprints() -> Dict[int, set]:
    """Pre-compute hash sets for every analyzed library track."""
    librosa = _librosa()
    out: Dict[int, set] = {}
    for tr in db.get_analyzed_tracks():
        path = tr.get("path")
        if not path or not Path(path).exists():
            continue
        try:
            y, sr = librosa.load(path, sr=SAMPLE_RATE, mono=True, duration=45)
            if len(y) < sr:
                continue
            lms = _chroma_landmarks(y, sr)
            hashes = _hashes_from_landmarks(lms)
            out[tr["id"]] = set(hashes)
        except Exception:
            continue
    return out


def _hashes_from_landmarks(landmarks: List[Tuple[int, int]]) -> List[str]:
    import hashlib
    out = []
    for i in range(len(landmarks) - 3):
        window = landmarks[i: i + 4]
        deltas = [window[j + 1][0] - window[j][0] for j in range(3)]
        peaks = [w[1] for w in window]
        payload = ",".join(map(str, peaks + deltas))
        out.append(hashlib.blake2b(payload.encode(), digest_size=4).hexdigest())
    return out


def recover_tracklist(
    set_path: str,
    window_sec: float = 30.0,
    step_sec: float = 15.0,
    min_confidence: float = 0.20,
) -> Dict[str, Any]:
    """
    Slide a `window_sec` window over the recording with `step_sec` hop,
    fingerprint each window, match against the library.
    Adjacent windows that match the same track are merged into a single
    tracklist entry.
    """
    librosa = _librosa()
    set_p = Path(set_path)
    if not set_p.exists():
        return {"error": f"Set file not found: {set_path}"}

    # Load full set audio (mono, downsampled for speed)
    y, sr = librosa.load(set_p, sr=SAMPLE_RATE, mono=True)
    duration = len(y) / sr
    if duration < window_sec * 2:
        return {"error": "Set too short to recover tracklist"}

    # Pre-cache library fingerprints
    lib_fps = _load_library_fingerprints()

    # Walk the set
    raw: List[Tuple[float, Optional[int], float]] = []  # (start, track_id, conf)
    t = 0.0
    while t + window_sec <= duration:
        chunk = y[int(t * sr): int((t + window_sec) * sr)]
        try:
            lms = _chroma_landmarks(chunk, sr)
            qhashes = set(_hashes_from_landmarks(lms))
        except Exception:
            t += step_sec
            continue

        best_id: Optional[int] = None
        best_score = 0.0
        for tid, lh in lib_fps.items():
            if not lh:
                continue
            inter = qhashes & lh
            base = max(1, min(len(qhashes), len(lh)))
            score = len(inter) / base
            if score > best_score:
                best_score = score
                best_id = tid

        if best_score >= min_confidence:
            raw.append((t, best_id, best_score))
        else:
            raw.append((t, None, best_score))
        t += step_sec

    # Merge consecutive same-track windows
    entries: List[TracklistEntry] = []
    for start, tid, conf in raw:
        if entries and entries[-1].track_id == tid:
            entries[-1].end_sec = start + window_sec
            entries[-1].confidence = max(entries[-1].confidence, conf)
        else:
            tr = db.get_track(tid) if tid else None
            entries.append(TracklistEntry(
                start_sec=start,
                end_sec=start + window_sec,
                track_id=tid,
                artist=tr.get("artist") if tr else None,
                title=tr.get("title") if tr else None,
                confidence=round(conf, 3),
            ))

    # Filter: drop "unknown" gaps shorter than 60 sec (just transitions)
    cleaned = []
    for e in entries:
        if e.track_id is None and (e.end_sec - e.start_sec) < 60:
            continue
        cleaned.append(e)

    return {
        "set_path": str(set_p),
        "duration_sec": round(duration, 2),
        "window_sec": window_sec,
        "step_sec": step_sec,
        "entries": [asdict(e) for e in cleaned],
        "matched_count": sum(1 for e in cleaned if e.track_id is not None),
    }


def format_as_text(tracklist: Dict[str, Any]) -> str:
    """Plain-text tracklist with mm:ss timestamps."""
    lines = [f"# Tracklist — {Path(tracklist['set_path']).stem}"]
    for e in tracklist.get("entries", []):
        m = int(e["start_sec"] // 60)
        s = int(e["start_sec"] % 60)
        ts = f"{m:02d}:{s:02d}"
        if e["track_id"]:
            lines.append(f"{ts}  {e['artist']} — {e['title']}  [{int(e['confidence']*100)}%]")
        else:
            lines.append(f"{ts}  ID? (low confidence)")
    return "\n".join(lines)


def format_as_1001tracklists(tracklist: Dict[str, Any]) -> str:
    """1001tracklists.com cue-sheet style: 'h:mm:ss Artist - Title'"""
    lines = []
    for e in tracklist.get("entries", []):
        if not e["track_id"]:
            continue
        h = int(e["start_sec"] // 3600)
        m = int((e["start_sec"] % 3600) // 60)
        s = int(e["start_sec"] % 60)
        ts = f"{h}:{m:02d}:{s:02d}"
        lines.append(f"{ts} {e['artist']} - {e['title']}")
    return "\n".join(lines)
