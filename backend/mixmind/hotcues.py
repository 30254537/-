"""
Auto Hot Cues — generate 8 professional-grade Cue Points per track.

A working DJ usually wants Hot Cues at:

  1. Intro Start    — first downbeat, where you can start mixing in
  2. Intro End      — first big change, end of the breaks-only intro
  3. Build-up       — riser / filter sweep before the first drop
  4. Drop 1         — first real chorus / bassline kick
  5. Breakdown      — the calm middle section
  6. Drop 2         — second drop / climax
  7. Last Hit       — final climax / signature line
  8. Outro Start    — where the outro tail begins (mix-out)

We map structural events from the analyzer into these 8 slots and
return them in a format that goes straight into Rekordbox / Serato
hot cue banks.

Heuristics rely on:
  - existing intro_end / first_drop / breakdown / outro_start (analyzer)
  - per-section RMS curve to detect the "second drop" and "build-up"
  - bar/phrase grid for snapping to a downbeat
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

import numpy as np

from mixmind import database as db
from mixmind.config import HOP_LENGTH, SAMPLE_RATE


# Standard Rekordbox hot cue colors (RGB hex). 8 slots, A..H.
DEFAULT_CUE_COLORS = [
    "0xFF0000",  # red       — intro
    "0xFF8800",  # orange    — intro end
    "0xFFD700",  # gold      — build-up
    "0xFF2EA6",  # neon pink — drop 1
    "0x00E5FF",  # neon blue — breakdown
    "0xFF2EA6",  # neon pink — drop 2
    "0xFFD700",  # gold      — last hit
    "0x9D00FF",  # purple    — outro
]

CUE_LABELS = [
    "Intro Start",
    "Intro End",
    "Build Up",
    "Drop 1",
    "Breakdown",
    "Drop 2",
    "Last Hit",
    "Outro Start",
]


@dataclass
class HotCue:
    slot: int            # 0..7
    name: str
    time_sec: float
    color: str
    type: str            # one of CUE_LABELS lowercased


def _load_audio(path: str):
    import librosa
    return librosa.load(path, sr=SAMPLE_RATE, mono=True)


def _rms_envelope(y: np.ndarray) -> np.ndarray:
    import librosa
    return librosa.feature.rms(y=y, hop_length=HOP_LENGTH)[0]


def _snap_to_downbeat(t: float, downbeats: List[float]) -> float:
    if not downbeats:
        return t
    return float(min(downbeats, key=lambda d: abs(d - t)))


def _detect_build_up(rms: np.ndarray, sr: int, drop_time: float) -> Optional[float]:
    """
    Build-up = sustained RMS rise lasting ~8 bars right before drop.
    We look at the 12 seconds before drop_time and find where the RMS
    first starts climbing monotonically.
    """
    fps = sr / HOP_LENGTH
    drop_frame = int(drop_time * fps)
    if drop_frame <= 0:
        return None
    win = int(12 * fps)
    start = max(0, drop_frame - win)
    seg = rms[start:drop_frame]
    if len(seg) < fps:
        return None
    # smooth
    k = max(2, int(fps / 4))
    ker = np.ones(k) / k
    sm = np.convolve(seg, ker, mode="same")
    # Find longest rising run
    rising = np.diff(sm) > 0
    best_start, best_len, cur_start, cur_len = 0, 0, 0, 0
    for i, r in enumerate(rising):
        if r:
            if cur_len == 0:
                cur_start = i
            cur_len += 1
            if cur_len > best_len:
                best_len = cur_len
                best_start = cur_start
        else:
            cur_len = 0
    if best_len < fps * 2:
        return None
    return (start + best_start) / fps


def _detect_second_drop(rms: np.ndarray, sr: int, after: float, duration: float) -> Optional[float]:
    """Find a peak RMS > 90th percentile in the second half of the track."""
    fps = sr / HOP_LENGTH
    start_f = int(after * fps)
    end_f = int(duration * 0.95 * fps)
    if end_f - start_f < fps * 8:
        return None
    seg = rms[start_f:end_f]
    if len(seg) == 0:
        return None
    smooth = np.convolve(seg, np.ones(int(fps * 2)) / int(max(1, fps * 2)), mode="same")
    thresh = np.percentile(smooth, 92)
    above = np.where(smooth >= thresh)[0]
    if len(above) == 0:
        return None
    # Pick first sustained section above threshold
    return (start_f + int(above[0])) / fps


def _detect_last_hit(rms: np.ndarray, sr: int, duration: float, outro_start: Optional[float]) -> Optional[float]:
    """
    Last big hit: final RMS peak before the outro, or in the last quarter
    if no outro is known.
    """
    fps = sr / HOP_LENGTH
    end_f = int((outro_start or duration * 0.92) * fps)
    start_f = int((outro_start or duration * 0.7) * fps - fps * 8)
    start_f = max(0, start_f)
    if end_f <= start_f:
        return None
    seg = rms[start_f:end_f]
    if len(seg) == 0:
        return None
    smooth = np.convolve(seg, np.ones(int(fps * 1.5)) / int(max(1, fps * 1.5)), mode="same")
    pk = int(np.argmax(smooth))
    return (start_f + pk) / fps


def generate_hot_cues(track_id: int) -> Dict[str, Any]:
    """Return 8 hot cues for the track."""
    track = db.get_track(track_id)
    if not track:
        return {"error": "Track not found"}
    path = track.get("path")
    if not path:
        return {"error": "No file path"}

    intro_end = track.get("intro_end")
    first_drop = track.get("first_drop")
    breakdown = track.get("breakdown")
    outro_start = track.get("outro_start")
    duration = track.get("duration") or 0
    downbeats_raw = track.get("downbeats")
    try:
        downbeats = json.loads(downbeats_raw) if isinstance(downbeats_raw, str) else (downbeats_raw or [])
    except Exception:
        downbeats = []

    # We need RMS to find build-up + drop2 + last hit, so load audio
    try:
        y, sr = _load_audio(path)
        rms = _rms_envelope(y)
    except Exception:
        return {"error": "Audio load failed"}

    cues: List[HotCue] = []

    # 1. Intro Start = first downbeat or 0
    intro_start_t = float(downbeats[0]) if downbeats else 0.0
    cues.append(HotCue(0, CUE_LABELS[0], round(intro_start_t, 3), DEFAULT_CUE_COLORS[0], "intro_start"))

    # 2. Intro End
    if intro_end:
        cues.append(HotCue(1, CUE_LABELS[1],
                           round(_snap_to_downbeat(intro_end, downbeats), 3),
                           DEFAULT_CUE_COLORS[1], "intro_end"))

    # 3. Build Up
    if first_drop:
        bu = _detect_build_up(rms, sr, first_drop)
        if bu is not None:
            cues.append(HotCue(2, CUE_LABELS[2],
                               round(_snap_to_downbeat(bu, downbeats), 3),
                               DEFAULT_CUE_COLORS[2], "build_up"))

    # 4. Drop 1
    if first_drop:
        cues.append(HotCue(3, CUE_LABELS[3],
                           round(_snap_to_downbeat(first_drop, downbeats), 3),
                           DEFAULT_CUE_COLORS[3], "drop_1"))

    # 5. Breakdown
    if breakdown:
        cues.append(HotCue(4, CUE_LABELS[4],
                           round(_snap_to_downbeat(breakdown, downbeats), 3),
                           DEFAULT_CUE_COLORS[4], "breakdown"))

    # 6. Drop 2
    after = breakdown or (first_drop or 0) + 30
    drop2 = _detect_second_drop(rms, sr, after, duration)
    if drop2:
        cues.append(HotCue(5, CUE_LABELS[5],
                           round(_snap_to_downbeat(drop2, downbeats), 3),
                           DEFAULT_CUE_COLORS[5], "drop_2"))

    # 7. Last Hit
    last_hit = _detect_last_hit(rms, sr, duration, outro_start)
    if last_hit:
        cues.append(HotCue(6, CUE_LABELS[6],
                           round(_snap_to_downbeat(last_hit, downbeats), 3),
                           DEFAULT_CUE_COLORS[6], "last_hit"))

    # 8. Outro Start
    if outro_start:
        cues.append(HotCue(7, CUE_LABELS[7],
                           round(_snap_to_downbeat(outro_start, downbeats), 3),
                           DEFAULT_CUE_COLORS[7], "outro_start"))

    # Sort by time and re-index slots so they remain ordered for export
    cues.sort(key=lambda c: c.time_sec)
    for i, c in enumerate(cues):
        c.slot = i

    return {
        "track_id": track_id,
        "duration": duration,
        "bpm": track.get("bpm"),
        "cues": [asdict(c) for c in cues],
    }


def write_cues_to_db(track_id: int, cues_payload: Dict[str, Any]):
    """Persist cue points back to the track row as JSON for export consumption."""
    cues = cues_payload.get("cues") or []
    db.update_track(track_id, {"hot_cues": json.dumps(cues)})
