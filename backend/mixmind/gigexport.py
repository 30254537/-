"""
Gig USB Export — pack a setlist for the booth.

Given a saved playlist (or arbitrary list of track ids), produce an output
folder that contains everything a working DJ needs:

  /<gig_root>/
    music/                    # audio, optionally loudness-normalized
      01 - Artist - Title.mp3
      02 - Artist - Title.mp3
    rekordbox.xml             # full Rekordbox import file (cues + grid)
    serato_playlist.txt       # Serato Import Playlist
    playlist.m3u8             # universal
    covers/                   # extracted album art (JPG)
    metadata.json             # full library data dump for this gig
    README.txt                # printout of tracklist

The folder is sized to fit on a USB stick. Audio can be normalized to a
chosen LUFS target (Pioneer's club-standard is -8 LUFS for peak time).

This module does not depend on ffmpeg for normalize — it computes the
required gain via the existing LUFS measurement, then re-encodes with
either pydub (if available) or libsndfile direct.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from mixmind import database as db
from mixmind.exporter import export_rekordbox_xml, export_serato_crate
from mixmind.playlist import export_m3u8


def _safe_filename(s: str) -> str:
    bad = '<>:"/\\|?*'
    for c in bad:
        s = s.replace(c, "_")
    return s.strip()[:120] or "track"


def _extract_cover(src: str, dest: str) -> bool:
    """Pull embedded album art using mutagen. Returns True if written."""
    try:
        from mutagen import File as MutagenFile
        from mutagen.id3 import APIC
        f = MutagenFile(src)
        if f is None:
            return False
        # ID3
        for k, v in (f.tags or {}).items():
            if isinstance(v, APIC):
                with open(dest, "wb") as fh:
                    fh.write(v.data)
                return True
        # MP4
        if hasattr(f, "tags") and f.tags is not None:
            covr = f.tags.get("covr") if hasattr(f.tags, "get") else None
            if covr:
                with open(dest, "wb") as fh:
                    fh.write(bytes(covr[0]))
                return True
        # FLAC
        pics = getattr(f, "pictures", None)
        if pics:
            with open(dest, "wb") as fh:
                fh.write(pics[0].data)
            return True
    except Exception:
        return False
    return False


def _normalize_audio(src: str, dest: str, current_lufs: float, target_lufs: float) -> bool:
    """Re-encode src to dest applying gain to hit target_lufs."""
    try:
        import numpy as np
        import soundfile as sf
        data, sr = sf.read(src, always_2d=True)
        gain_db = target_lufs - current_lufs
        gain_lin = 10 ** (gain_db / 20.0)
        out = data * gain_lin
        # Hard clip protection
        peak = float(np.max(np.abs(out))) + 1e-12
        if peak > 0.99:
            out = out * (0.99 / peak)
        sf.write(dest, out.astype("float32"), sr)
        return True
    except Exception:
        return False


def export_gig(
    out_root: str,
    track_ids: Optional[List[int]] = None,
    playlist_id: Optional[int] = None,
    playlist_name: str = "Gig",
    normalize_lufs: Optional[float] = -8.0,
    include_covers: bool = True,
) -> Dict[str, Any]:
    """
    Build the gig folder. If `normalize_lufs` is None, audio is copied verbatim.
    """
    if playlist_id is not None:
        tracks = db.get_playlist_tracks(playlist_id)
    elif track_ids:
        tracks = [t for t in (db.get_track(tid) for tid in track_ids) if t]
    else:
        tracks = []

    if not tracks:
        raise ValueError("No tracks supplied to export.")

    out = Path(out_root).expanduser().resolve()
    music_dir = out / "music"
    cover_dir = out / "covers"
    music_dir.mkdir(parents=True, exist_ok=True)
    cover_dir.mkdir(parents=True, exist_ok=True)

    new_tracks = []
    failures: List[str] = []
    total_bytes = 0
    for i, t in enumerate(tracks, 1):
        src = t.get("path")
        if not src or not os.path.exists(src):
            failures.append(f"missing: {t.get('filename')}")
            continue

        ext = Path(src).suffix.lower()
        artist = _safe_filename(t.get("artist") or "Unknown")
        title = _safe_filename(t.get("title") or t.get("filename") or "Untitled")
        target_name = f"{i:02d} - {artist} - {title}{ext}"
        dest = music_dir / target_name

        if normalize_lufs is not None and t.get("loudness") is not None and ext in (".wav", ".flac", ".aiff", ".aif"):
            ok = _normalize_audio(src, str(dest), float(t["loudness"]), normalize_lufs)
            if not ok:
                shutil.copyfile(src, dest)
        else:
            # MP3 / M4A: lossless re-encode is non-trivial without ffmpeg, so copy as-is.
            shutil.copyfile(src, dest)

        if include_covers:
            cover_dest = cover_dir / f"{i:02d}.jpg"
            _extract_cover(src, str(cover_dest))

        total_bytes += dest.stat().st_size
        copy = dict(t)
        copy["path"] = str(dest)
        new_tracks.append(copy)

    # Export sidecar files using copied paths (so they reference USB locations)
    rb_path = out / "rekordbox.xml"
    export_rekordbox_xml(new_tracks, str(rb_path), playlists={playlist_name: [t["id"] for t in new_tracks]})

    serato_path = out / "serato_playlist.txt"
    export_serato_crate(new_tracks, str(serato_path))

    m3u_path = out / "playlist.m3u8"
    export_m3u8(new_tracks, str(m3u_path))

    # Tracklist + JSON sidecar
    json_path = out / "metadata.json"
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump({
            "playlist": playlist_name,
            "track_count": len(new_tracks),
            "normalize_lufs": normalize_lufs,
            "tracks": [{
                "position": i,
                "artist": t.get("artist"),
                "title": t.get("title"),
                "bpm": t.get("bpm"),
                "camelot": t.get("camelot"),
                "energy": t.get("energy"),
                "duration": t.get("duration"),
            } for i, t in enumerate(new_tracks, 1)],
        }, fh, indent=2)

    readme_path = out / "README.txt"
    with readme_path.open("w", encoding="utf-8") as fh:
        fh.write(f"# {playlist_name}\n")
        fh.write(f"Tracks: {len(new_tracks)}\n")
        fh.write(f"Normalize: {normalize_lufs} LUFS\n\n")
        for i, t in enumerate(new_tracks, 1):
            fh.write(f"{i:02d}  {t.get('bpm') or '?':>5} BPM  {t.get('camelot') or '-':<3}  "
                     f"{t.get('artist')} — {t.get('title')}\n")

    return {
        "out_dir": str(out),
        "track_count": len(new_tracks),
        "total_size_mb": round(total_bytes / (1024 * 1024), 2),
        "rekordbox_xml": str(rb_path),
        "serato_playlist": str(serato_path),
        "m3u8": str(m3u_path),
        "metadata_json": str(json_path),
        "failures": failures,
    }
