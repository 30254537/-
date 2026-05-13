"""
Style Reverse-Engineering — analyze a song's section-by-section structure for
producers/DJ-producers who want to understand how a track is built.

Per section (intro / verse / drop / breakdown / outro):
  - Average RMS in dB
  - Spectral centroid (brightness)
  - Energy in low/mid/high bands (kick / mids / hi-hats)
  - Tempo stability
  - Onset density (busy vs sparse)

Output: a per-section breakdown that highlights "what changes between sections".
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

import numpy as np

from mixmind import database as db
from mixmind.config import HOP_LENGTH, SAMPLE_RATE


@dataclass
class SectionStats:
    label: str
    start_sec: float
    end_sec: float
    duration_sec: float
    rms_db: float
    centroid_hz: float
    low_energy_pct: float       # % energy in <250 Hz
    mid_energy_pct: float       # % energy in 250-2500 Hz
    high_energy_pct: float      # % energy in >2500 Hz
    onset_density: float        # onsets/sec


def _librosa():
    import librosa
    return librosa


def analyze_track_sections(track_id: int) -> Dict[str, Any]:
    track = db.get_track(track_id)
    if not track:
        return {"error": "Track not found"}
    path = track.get("path")
    if not path:
        return {"error": "No path"}

    librosa = _librosa()
    y, sr = librosa.load(path, sr=SAMPLE_RATE, mono=True)
    duration = len(y) / sr

    # Section ranges from existing structural cues
    intro_end = float(track.get("intro_end") or duration * 0.15)
    first_drop = float(track.get("first_drop") or intro_end + 16)
    breakdown = float(track.get("breakdown") or first_drop + (duration * 0.3))
    outro_start = float(track.get("outro_start") or duration * 0.85)

    sections: List[Dict[str, float]] = [
        {"label": "intro",     "start_sec": 0.0,             "end_sec": intro_end},
        {"label": "drop_1",    "start_sec": intro_end,       "end_sec": breakdown},
        {"label": "breakdown", "start_sec": breakdown,       "end_sec": min(breakdown + 32, outro_start)},
        {"label": "drop_2",    "start_sec": min(breakdown + 32, outro_start), "end_sec": outro_start},
        {"label": "outro",     "start_sec": outro_start,     "end_sec": duration},
    ]
    sections = [s for s in sections if s["end_sec"] > s["start_sec"]]

    # Pre-compute features once
    stft = np.abs(librosa.stft(y, hop_length=HOP_LENGTH))
    freqs = librosa.fft_frequencies(sr=sr)
    rms_full = librosa.feature.rms(y=y, hop_length=HOP_LENGTH)[0]
    centroid_full = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=HOP_LENGTH)[0]
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=HOP_LENGTH)
    onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=HOP_LENGTH)
    onset_times = librosa.frames_to_time(onsets, sr=sr, hop_length=HOP_LENGTH)

    fps = sr / HOP_LENGTH
    out: List[SectionStats] = []
    for s in sections:
        f0, f1 = int(s["start_sec"] * fps), int(s["end_sec"] * fps)
        f1 = min(f1, stft.shape[1])
        if f1 <= f0:
            continue

        rms_seg = rms_full[f0:f1]
        rms_db = 20 * np.log10(np.mean(rms_seg) + 1e-8)

        cent_seg = centroid_full[f0:f1]
        cent = float(np.mean(cent_seg))

        spec_seg = stft[:, f0:f1]
        low = spec_seg[freqs < 250].sum()
        mid = spec_seg[(freqs >= 250) & (freqs < 2500)].sum()
        high = spec_seg[freqs >= 2500].sum()
        total = float(low + mid + high) + 1e-8

        n_onsets = int(np.sum((onset_times >= s["start_sec"]) & (onset_times < s["end_sec"])))
        sec_dur = s["end_sec"] - s["start_sec"]
        density = n_onsets / max(sec_dur, 1)

        out.append(SectionStats(
            label=s["label"],
            start_sec=round(s["start_sec"], 2),
            end_sec=round(s["end_sec"], 2),
            duration_sec=round(sec_dur, 2),
            rms_db=round(float(rms_db), 2),
            centroid_hz=round(cent, 1),
            low_energy_pct=round(float(low / total) * 100, 1),
            mid_energy_pct=round(float(mid / total) * 100, 1),
            high_energy_pct=round(float(high / total) * 100, 1),
            onset_density=round(float(density), 2),
        ))

    return {
        "track_id": track_id,
        "duration_sec": round(duration, 2),
        "sections": [asdict(s) for s in out],
    }
