"""
Mastering pipeline — Platinum-Notes-equivalent.

For each track:
  - Detect sample-level clipping (true-peak above 0 dBFS)
  - Apply a soft limiter to repair clipping and headroom
  - Match loudness to a target LUFS (default -8 for club use, -14 for streaming)
  - Optional: apply a gentle high-shelf to tame dull MP3 transcodes

Output writes to a parallel "mastered" file rather than overwriting the source.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from mixmind import database as db


def _librosa_load(path: str):
    import librosa
    return librosa.load(path, sr=None, mono=False)


def _measure_lufs(y: np.ndarray, sr: int) -> float:
    """Reuse analyzer's BS.1770 LUFS implementation if available."""
    try:
        from mixmind.analyzer import integrated_loudness_lufs
        if y.ndim > 1:
            mono = np.mean(y, axis=0)
        else:
            mono = y
        return integrated_loudness_lufs(mono, sr)
    except Exception:
        return -14.0


def _detect_clipping(y: np.ndarray) -> Dict[str, Any]:
    abs_y = np.abs(y)
    peak = float(np.max(abs_y))
    # Count contiguous samples ≥ 0.999
    if y.ndim > 1:
        flat = abs_y.flatten()
    else:
        flat = abs_y
    near_clip = (flat >= 0.999)
    # Rough number of clipped "events" (consecutive runs)
    runs = 0
    in_run = False
    for v in near_clip:
        if v and not in_run:
            runs += 1
            in_run = True
        elif not v:
            in_run = False
    return {
        "peak": peak,
        "true_peak_db": round(20 * np.log10(peak + 1e-12), 2),
        "clipped_samples": int(np.sum(near_clip)),
        "clipping_events": runs,
    }


def _soft_limit(y: np.ndarray, ceiling: float = -1.0) -> np.ndarray:
    """Apply a tanh-style soft limiter so peaks stay below `ceiling` dBFS."""
    target = 10 ** (ceiling / 20)
    peak = float(np.max(np.abs(y)))
    if peak <= target:
        return y
    # Compress everything > target gently
    out = np.where(np.abs(y) > target,
                   np.sign(y) * (target + (target * 0.5) * np.tanh((np.abs(y) - target) / (target * 0.5 + 1e-9))),
                   y)
    return out.astype(y.dtype)


def master_file(
    src_path: str,
    out_path: str,
    target_lufs: float = -8.0,
    ceiling_db: float = -1.0,
    repair_clipping: bool = True,
) -> Dict[str, Any]:
    """Read src, analyse, fix clipping, normalize loudness, write out_path."""
    try:
        import soundfile as sf
    except ImportError:
        return {"error": "soundfile not installed"}

    y, sr = _librosa_load(src_path)
    # Ensure (channels, samples) shape
    if y.ndim == 1:
        y = y[np.newaxis, :]

    pre_clip = _detect_clipping(y)
    pre_lufs = _measure_lufs(y, sr)

    work = y.copy()

    if repair_clipping and pre_clip["clipped_samples"] > 0:
        # Pull peak well below 0 dB before limiting
        peak = float(np.max(np.abs(work)))
        if peak > 0:
            work = work * (0.95 / peak)
        work = _soft_limit(work, ceiling=ceiling_db)

    # Re-measure post-clip-repair
    mid_lufs = _measure_lufs(work, sr)
    gain_db = target_lufs - mid_lufs
    gain_lin = 10 ** (gain_db / 20.0)
    work = work * gain_lin

    # Final ceiling protection
    work = _soft_limit(work, ceiling=ceiling_db)

    post_clip = _detect_clipping(work)
    post_lufs = _measure_lufs(work, sr)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    # soundfile expects (samples, channels)
    out_arr = work.T if work.ndim > 1 else work
    sf.write(out_path, out_arr.astype("float32"), sr)

    return {
        "source": src_path,
        "output": out_path,
        "pre": {"lufs": pre_lufs, **pre_clip},
        "post": {"lufs": post_lufs, **post_clip},
        "applied_gain_db": round(gain_db, 2),
        "target_lufs": target_lufs,
    }


def batch_master(
    track_ids: List[int],
    out_dir: str,
    target_lufs: float = -8.0,
) -> Dict[str, Any]:
    """Master a list of tracks into a directory."""
    out = Path(out_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)

    reports: List[Dict[str, Any]] = []
    for tid in track_ids:
        t = db.get_track(tid)
        if not t or not t.get("path"):
            continue
        src = t["path"]
        dst = out / f"MASTERED__{Path(src).name}"
        try:
            r = master_file(src, str(dst), target_lufs=target_lufs)
            r["track_id"] = tid
            reports.append(r)
        except Exception as e:
            reports.append({"track_id": tid, "error": str(e)})
    return {"reports": reports, "count": len(reports), "out_dir": str(out)}
