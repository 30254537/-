"""
Highlight Reel — auto-extract the most exciting 30-second clip from a long set.

Method:
  - Compute RMS envelope across the entire set
  - Compute spectral centroid (energy in mid-high frequencies)
  - Compute onset density (rhythmic activity)
  - Combine into a "hype score" curve
  - Find the highest sustained 30-second window
  - Optionally trim and write a clip + waveform image

This is what you post to Instagram / TikTok the morning after a gig.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from mixmind.config import HOP_LENGTH, SAMPLE_RATE


@dataclass
class HighlightClip:
    source_path: str
    clip_start_sec: float
    clip_end_sec: float
    clip_duration_sec: float
    hype_score: float
    output_path: Optional[str] = None


def _librosa():
    import librosa
    return librosa


def find_highlight(
    set_path: str,
    clip_seconds: float = 30.0,
    n_top: int = 1,
) -> Dict[str, Any]:
    """
    Identify the top-N most exciting clip(s) of `clip_seconds` length.
    Returns metadata only; doesn't write audio.
    """
    librosa = _librosa()
    p = Path(set_path)
    if not p.exists():
        return {"error": f"Not found: {set_path}"}

    y, sr = librosa.load(p, sr=SAMPLE_RATE, mono=True)
    duration = len(y) / sr
    if duration < clip_seconds + 5:
        return {"error": "Set too short"}

    # 1. RMS energy
    rms = librosa.feature.rms(y=y, hop_length=HOP_LENGTH)[0]
    # 2. Spectral centroid
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=HOP_LENGTH)[0]
    # 3. Onset envelope
    onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=HOP_LENGTH)

    # Normalize each to 0..1
    def _norm(x):
        x = np.asarray(x, dtype=float)
        m, M = x.min(), x.max()
        return (x - m) / (M - m + 1e-8)

    n = min(len(rms), len(centroid), len(onset))
    rms = _norm(rms[:n])
    centroid = _norm(centroid[:n])
    onset = _norm(onset[:n])

    hype = rms * 0.5 + centroid * 0.2 + onset * 0.3

    # Smooth across `clip_seconds` window
    fps = sr / HOP_LENGTH
    window = max(1, int(clip_seconds * fps))
    if len(hype) < window:
        return {"error": "Set too short"}
    kernel = np.ones(window) / window
    smoothed = np.convolve(hype, kernel, mode="valid")

    # Top-N peaks separated by at least clip_seconds
    picks = []
    s = smoothed.copy()
    for _ in range(n_top):
        if len(s) == 0:
            break
        i = int(np.argmax(s))
        score = float(s[i])
        start_sec = i / fps
        picks.append({
            "start_sec": round(start_sec, 2),
            "end_sec": round(start_sec + clip_seconds, 2),
            "duration_sec": clip_seconds,
            "hype_score": round(score, 4),
        })
        # Mask out window around chosen peak
        lo = max(0, i - window)
        hi = min(len(s), i + window)
        s[lo:hi] = -np.inf

    return {
        "source_path": str(p),
        "set_duration_sec": round(duration, 2),
        "clips": picks,
    }


def export_clip(
    set_path: str,
    out_path: str,
    start_sec: float,
    duration_sec: float = 30.0,
) -> str:
    """Trim and write the highlight to a WAV file."""
    librosa = _librosa()
    import soundfile as sf
    y, sr = librosa.load(set_path, sr=SAMPLE_RATE, mono=False)
    if y.ndim == 1:
        y = y[np.newaxis, :]
    n_start = int(start_sec * sr)
    n_end = int((start_sec + duration_sec) * sr)
    n_end = min(n_end, y.shape[-1])
    clip = y[..., n_start:n_end]
    # Apply a tiny 100 ms fade in/out so it doesn't click
    fade_n = int(0.1 * sr)
    if clip.shape[-1] > fade_n * 2:
        ramp = np.linspace(0, 1, fade_n)
        clip[..., :fade_n] *= ramp
        clip[..., -fade_n:] *= ramp[::-1]
    sf.write(out_path, clip.T if clip.ndim > 1 else clip, sr)
    return out_path
