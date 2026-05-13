"""
Quality Audit — detect upsampled / fake high-bitrate files.

A genuine 320 kbps MP3 retains spectral content up to ~20 kHz. A 128
or 192 kbps file converted to 320 still has its high-frequency content
killed by the original encoder (lowpass at ~16 kHz for 128k, ~18 kHz
for 192k). The fake file therefore shows a sharp, flat brick-wall
above its true cutoff, regardless of the new container's bitrate.

This module:

  * Computes the spectrum of the audio
  * Finds the highest frequency bin that is consistently present
    (above a noise floor) over the full track
  * Flags files where this cutoff is well below 20 kHz despite a
    container that claims a high bitrate

We also report:
  - declared bitrate (from mutagen)
  - measured spectral cutoff
  - container format / sample rate
  - quality verdict: pristine / lossy_320 / fake_320 / very_lossy

Real numbers, no heuristics dressed up as facts: the reported cutoff is
measured directly off the spectrum.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class QualityReport:
    path: str
    declared_bitrate_kbps: Optional[int]
    container: str
    sample_rate: int
    measured_cutoff_hz: float
    verdict: str
    score: float                  # 0..1, 1 = pristine
    notes: List[str]
    spectrum_db: List[float]      # downsampled for display


def _librosa():
    import librosa
    return librosa


def _container_info(path: str) -> Dict[str, Any]:
    """Pull container metadata via mutagen."""
    try:
        from mutagen import File as MutagenFile
        f = MutagenFile(path)
        if f is None or f.info is None:
            return {}
        info = f.info
        bitrate = getattr(info, "bitrate", 0) or 0
        sr = getattr(info, "sample_rate", 0) or 0
        codec = type(f).__name__
        return {
            "bitrate_kbps": int(bitrate / 1000) if bitrate else None,
            "sample_rate": int(sr) if sr else 0,
            "container": codec,
        }
    except Exception:
        return {}


def _spectral_cutoff(y: np.ndarray, sr: int, noise_db: float = -75.0) -> float:
    """
    Return the highest frequency where the long-term magnitude spectrum
    is consistently above noise_db. We average power across time to get
    a stable estimate even with silence / drops.
    """
    librosa = _librosa()
    S = np.abs(librosa.stft(y, n_fft=4096, hop_length=2048))
    # Average over time, then convert to dB relative to peak
    avg = S.mean(axis=1)
    peak = np.max(avg) + 1e-12
    db = 20 * np.log10(avg / peak + 1e-12)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=4096)
    # Walk down from highest bin until we cross above noise floor
    above = np.where(db > noise_db)[0]
    if len(above) == 0:
        return 0.0
    return float(freqs[above[-1]])


def _verdict(cutoff: float, declared_kbps: Optional[int], sr: int) -> Dict[str, Any]:
    """Classify the file given measured cutoff vs claimed bitrate."""
    notes: List[str] = []
    nyquist = sr / 2
    score = 1.0

    # Reality cap due to sample rate
    if cutoff >= nyquist * 0.95:
        score = min(score, 1.0)
    if cutoff < 16500:
        score -= 0.30
        notes.append(f"high-end killed at {cutoff:.0f} Hz (likely 128 kbps source)")
    elif cutoff < 18500:
        score -= 0.15
        notes.append(f"cutoff at {cutoff:.0f} Hz suggests 192 kbps source")
    elif cutoff < 20000:
        notes.append(f"cutoff at {cutoff:.0f} Hz — typical of 320 kbps MP3")

    if declared_kbps and declared_kbps >= 300 and cutoff < 16500:
        notes.append("FAKE 320: declared high bitrate but spectrum says <=128 kbps source")
        verdict = "fake_320"
        score = min(score, 0.25)
    elif declared_kbps and declared_kbps >= 300 and cutoff < 18500:
        verdict = "fake_320"
        notes.append("Suspicious: 320 declared but spectrum suggests 192 kbps source")
        score = min(score, 0.55)
    elif declared_kbps and declared_kbps >= 1000:
        verdict = "lossless"
    elif declared_kbps and declared_kbps >= 280:
        verdict = "lossy_320"
    elif declared_kbps and declared_kbps < 200:
        verdict = "very_lossy"
        score = min(score, 0.5)
    else:
        verdict = "lossy"

    return {"verdict": verdict, "notes": notes, "score": round(max(0.0, score), 3)}


def audit_file(path: str, max_seconds: float = 60.0) -> Dict[str, Any]:
    librosa = _librosa()
    info = _container_info(path)
    y, sr = librosa.load(path, sr=None, mono=True, duration=max_seconds)
    cutoff = _spectral_cutoff(y, sr)
    classified = _verdict(cutoff, info.get("bitrate_kbps"), sr)

    # Downsampled spectrum for UI display (200 points, in dB)
    S = np.abs(librosa.stft(y, n_fft=4096, hop_length=2048)).mean(axis=1)
    peak = np.max(S) + 1e-12
    db = 20 * np.log10(S / peak + 1e-12)
    if len(db) > 200:
        bucket = len(db) // 200
        trimmed = db[: bucket * (len(db) // bucket)]
        db = trimmed.reshape(-1, bucket).mean(axis=1)

    report = QualityReport(
        path=path,
        declared_bitrate_kbps=info.get("bitrate_kbps"),
        container=info.get("container", Path(path).suffix.lstrip(".")),
        sample_rate=info.get("sample_rate", sr),
        measured_cutoff_hz=round(cutoff, 1),
        verdict=classified["verdict"],
        score=classified["score"],
        notes=classified["notes"],
        spectrum_db=[round(float(x), 2) for x in db],
    )
    return asdict(report)


def audit_library(track_ids: Optional[List[int]] = None,
                  limit: int = 200) -> List[Dict[str, Any]]:
    """Run audits across many tracks and return summary records."""
    from mixmind import database as db
    if track_ids:
        tracks = [t for t in (db.get_track(tid) for tid in track_ids) if t]
    else:
        tracks = db.find_tracks(limit=limit)

    results: List[Dict[str, Any]] = []
    for t in tracks:
        path = t.get("path")
        if not path:
            continue
        try:
            r = audit_file(path)
            r["track_id"] = t["id"]
            r["title"] = t.get("title")
            r["artist"] = t.get("artist")
            results.append(r)
        except Exception as e:
            results.append({
                "track_id": t["id"], "title": t.get("title"),
                "artist": t.get("artist"), "verdict": "error",
                "notes": [str(e)],
            })
    return results
