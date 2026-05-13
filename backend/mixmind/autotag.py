"""
Auto-tagger — intelligently move/copy new downloads into a clean folder structure.

Given a chaotic "NewDownloads" folder, organize files into:

  /Music/
    Tech House/
      122-126 BPM/
      126-130 BPM/
    Techno/
      Peak Time/
      Driving/
    ...

Filename normalization: "Artist - Title (Mix Name).ext".

Modes:
  - dry_run: returns the planned moves without touching disk
  - move: actually moves files (default behavior is COPY for safety)
  - copy: copies, leaves originals alone
"""
from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from mixmind import database as db


# Folder buckets per genre
GENRE_BUCKETS: Dict[str, List[str]] = {
    "Tech House": ["122-126 BPM", "126-130 BPM", "130+ BPM"],
    "House": ["118-122 BPM", "122-126 BPM"],
    "Deep House": ["118-122 BPM", "122-126 BPM"],
    "Progressive House": ["124-128 BPM", "128-132 BPM"],
    "Techno": ["Peak Time", "Driving", "Hypnotic"],
    "Minimal Techno": ["Peak Time", "Driving"],
    "Trance": ["Vocal", "Uplifting", "Psy"],
    "Drum & Bass": ["Liquid", "Neuro", "Jump Up"],
    "Dubstep": ["Riddim", "Melodic"],
    "Hip-Hop": ["Old School", "Modern", "Trap"],
    "Trap": ["Hard", "Melodic"],
    "R&B": ["Classic", "Modern"],
    "Pop": ["Mainstream"],
    "Disco": ["Classic", "Nu-Disco"],
    "Reggaeton": ["Classic", "Modern"],
    "Afro House": ["Soulful", "Driving"],
    "Ambient": ["Drone", "Cinematic"],
    "Chillout": ["Lounge", "Downtempo"],
    "Breakbeat": ["Funky", "Hard"],
    "Hardstyle": ["Euphoric", "Raw"],
    "Electro": ["Modern", "Classic"],
    "Future Bass": ["Melodic", "Hard"],
}


def _bucket_for(track: Dict[str, Any]) -> str:
    """Pick a sub-bucket for a track within its genre."""
    genre = track.get("genre_ai") or "Unknown"
    bpm = track.get("bpm") or 0
    energy = track.get("energy") or 0
    brightness = track.get("brightness") or 0.5

    # BPM-based buckets
    if genre == "Tech House":
        if bpm < 126: return "122-126 BPM"
        if bpm < 130: return "126-130 BPM"
        return "130+ BPM"
    if genre in ("House", "Deep House"):
        return "118-122 BPM" if bpm < 122 else "122-126 BPM"
    if genre == "Progressive House":
        return "124-128 BPM" if bpm < 128 else "128-132 BPM"

    # Style-based buckets
    if genre == "Techno":
        if energy >= 8: return "Peak Time"
        if brightness > 0.55: return "Driving"
        return "Hypnotic"
    if genre == "Minimal Techno":
        return "Peak Time" if energy >= 7 else "Driving"
    if genre == "Trance":
        if bpm >= 142: return "Psy"
        if brightness > 0.6: return "Uplifting"
        return "Vocal"
    if genre == "Drum & Bass":
        if energy >= 8.5: return "Neuro"
        if brightness > 0.6: return "Jump Up"
        return "Liquid"

    # Generic fallback — use first bucket
    return GENRE_BUCKETS.get(genre, ["Unsorted"])[0]


def _safe_filename(s: str) -> str:
    bad = '<>:"/\\|?*'
    for c in bad:
        s = s.replace(c, "_")
    return s.strip()[:120] or "track"


def _normalized_filename(track: Dict[str, Any]) -> str:
    artist = _safe_filename(track.get("artist") or "Unknown")
    title = _safe_filename(track.get("title") or track.get("filename") or "Untitled")
    ext = Path(track.get("path") or "").suffix or ".mp3"
    return f"{artist} - {title}{ext}"


@dataclass
class TagPlan:
    track_id: int
    src_path: str
    dst_path: str
    genre: str
    bucket: str
    action: str  # copy | move | skip


def plan_organization(out_root: str, track_ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    """Build a plan of where each track should go. Doesn't touch disk."""
    out_path = Path(out_root).expanduser()
    if track_ids:
        tracks = [t for t in (db.get_track(tid) for tid in track_ids) if t]
    else:
        tracks = db.find_tracks(limit=100000)

    plans: List[TagPlan] = []
    for t in tracks:
        if not t.get("genre_ai") or not t.get("bpm"):
            plans.append(TagPlan(
                track_id=t["id"],
                src_path=t["path"],
                dst_path="",
                genre="(not analyzed)",
                bucket="",
                action="skip",
            ))
            continue
        bucket = _bucket_for(t)
        new_name = _normalized_filename(t)
        dst = out_path / t["genre_ai"] / bucket / new_name
        plans.append(TagPlan(
            track_id=t["id"],
            src_path=t["path"],
            dst_path=str(dst),
            genre=t["genre_ai"],
            bucket=bucket,
            action="copy",
        ))
    return [asdict(p) for p in plans]


def execute_organization(
    out_root: str,
    track_ids: Optional[List[int]] = None,
    mode: str = "copy",
    update_paths: bool = False,
) -> Dict[str, Any]:
    """
    Actually perform copies/moves. mode = "copy" (safe) or "move".
    If update_paths is True, the database is updated to point at the new locations.
    """
    if mode not in ("copy", "move"):
        raise ValueError("mode must be 'copy' or 'move'")

    plans = plan_organization(out_root, track_ids=track_ids)
    moved = 0
    failed: List[str] = []
    skipped = 0

    for p in plans:
        if p["action"] == "skip":
            skipped += 1
            continue
        try:
            dst = Path(p["dst_path"])
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                # Avoid clobber — append suffix
                stem, ext = dst.stem, dst.suffix
                k = 1
                while dst.exists():
                    dst = dst.parent / f"{stem} ({k}){ext}"
                    k += 1
            if mode == "copy":
                shutil.copy2(p["src_path"], dst)
            else:
                shutil.move(p["src_path"], dst)
            moved += 1
            if update_paths:
                db.update_track(p["track_id"], {"path": str(dst)})
        except Exception as e:
            failed.append(f"{p['src_path']}: {e}")

    return {
        "planned": len(plans),
        "executed": moved,
        "skipped": skipped,
        "failures": failed,
        "out_root": str(Path(out_root).expanduser()),
        "mode": mode,
    }
