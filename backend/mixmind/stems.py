"""
AI Stems — 4-track source separation for mashup / acapella / instrumental work.

Two backends, picked at runtime in this order:

  1. **Demucs (htdemucs)** — Facebook AI's hybrid spectrogram/waveform model.
     Best quality, runs on CPU or GPU. Produces vocals / drums / bass / other.

  2. **Spleeter** — Deezer's older Tensorflow model. Lower quality but works
     fine on weak machines.

If neither is installed we still expose the API, but `available=False` is
returned so the UI can show install instructions.

Outputs are written next to the source file as `<name>_stems/<stem>.wav`.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


STEM_NAMES = ["vocals", "drums", "bass", "other"]


@dataclass
class StemJob:
    track_path: str
    out_dir: str
    stems: Dict[str, str]
    backend: str
    duration_sec: Optional[float] = None


def detect_backend() -> Optional[str]:
    """Return the first available backend name."""
    try:
        import demucs.pretrained          # noqa: F401
        return "demucs"
    except ImportError:
        pass
    try:
        import spleeter                   # noqa: F401
        return "spleeter"
    except ImportError:
        pass
    return None


def get_capabilities() -> Dict[str, Any]:
    backend = detect_backend()
    return {
        "available": backend is not None,
        "backend": backend,
        "stems": STEM_NAMES,
        "install_hint": (
            "pip install demucs  # recommended (~2GB model on first run)"
            if backend is None else None
        ),
    }


def _separate_demucs(track_path: str, out_dir: str) -> Dict[str, str]:
    """Run htdemucs via its CLI for portability."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    # demucs CLI writes to ./separated/<model>/<track-name>/
    cmd = [
        "python", "-m", "demucs",
        "-n", "htdemucs",
        "-o", str(out),
        track_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    name = Path(track_path).stem
    base = out / "htdemucs" / name
    return {s: str(base / f"{s}.wav") for s in STEM_NAMES if (base / f"{s}.wav").exists()}


def _separate_spleeter(track_path: str, out_dir: str) -> Dict[str, str]:
    from spleeter.separator import Separator
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    sep = Separator("spleeter:4stems")
    sep.separate_to_file(track_path, str(out))
    name = Path(track_path).stem
    base = out / name
    mapping = {"vocals": "vocals.wav", "drums": "drums.wav",
               "bass": "bass.wav", "other": "other.wav"}
    return {s: str(base / fn) for s, fn in mapping.items() if (base / fn).exists()}


def separate(track_path: str, out_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Run 4-stem separation. Returns a StemJob-as-dict including paths.
    Throws RuntimeError if no backend is installed.
    """
    backend = detect_backend()
    if backend is None:
        raise RuntimeError(
            "No stem-separation backend installed. Install with: pip install demucs"
        )

    if out_dir is None:
        track = Path(track_path)
        out_dir = str(track.parent / f"{track.stem}_stems")

    if backend == "demucs":
        stems = _separate_demucs(track_path, out_dir)
    else:
        stems = _separate_spleeter(track_path, out_dir)

    return asdict(StemJob(
        track_path=track_path,
        out_dir=out_dir,
        stems=stems,
        backend=backend,
    ))


def make_acapella_mix(stems: Dict[str, str], out_path: str) -> str:
    """Vocals only → acapella file, by copying the vocals stem."""
    src = stems.get("vocals")
    if not src or not os.path.exists(src):
        raise FileNotFoundError("Vocals stem not produced.")
    shutil.copyfile(src, out_path)
    return out_path


def make_instrumental_mix(stems: Dict[str, str], out_path: str) -> str:
    """Sum of drums + bass + other → instrumental, with no vocals."""
    import numpy as np
    import soundfile as sf
    needed = [stems.get(k) for k in ("drums", "bass", "other") if stems.get(k)]
    if not needed:
        raise FileNotFoundError("No instrumental stems to mix.")
    mix = None
    sr = None
    for p in needed:
        data, this_sr = sf.read(p, always_2d=True)
        if mix is None:
            mix = np.zeros_like(data, dtype=np.float64)
            sr = this_sr
        # In case different lengths, trim to the shortest
        n = min(len(mix), len(data))
        mix = mix[:n] + data[:n]
    # Normalize to avoid clipping
    peak = float(np.max(np.abs(mix))) + 1e-12
    if peak > 0.99:
        mix = mix * (0.99 / peak)
    sf.write(out_path, mix.astype("float32"), sr)
    return out_path
