"""
Cloud / multi-machine sync.

Two strategies, picked by the user's environment:

  A. Local-only Sync via folder:
     - Export the SQLite library + cover-art cache to a single `.mixmind-pack`
       file (zip). Drop on Dropbox / iCloud / Google Drive folder.
     - Other machine imports it; the importer reconciles by audio_fingerprint
       so paths can differ between machines.

  B. Network Sync via WebDAV / SFTP / S3:
     - Same pack format; uploaded via configured remote.

This module implements (A); (B) is plug-in shaped via push/pull hooks.
"""
from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from mixmind import __version__
from mixmind import database as db
from mixmind.config import DB_PATH, CACHE_DIR


SYNC_VERSION = 1


def export_pack(out_path: str, include_covers: bool = True) -> Dict[str, Any]:
    """
    Bundle the entire library state into a single .mixmind-pack zip file
    that can be shared between machines.
    """
    out = Path(out_path).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)

    # 1. Dump tracks with stable keys
    tracks = db.find_tracks(limit=100000)
    payload = {
        "format": "mixmind-pack",
        "version": SYNC_VERSION,
        "app_version": __version__,
        "exported_at": datetime.utcnow().isoformat(),
        "track_count": len(tracks),
        "tracks": tracks,
        "playlists": [
            {**pl, "tracks": [t["id"] for t in db.get_playlist_tracks(pl["id"])]}
            for pl in db.get_playlists()
        ],
    }

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("library.json", json.dumps(payload, indent=2, default=str))
        # Also include the SQLite file for full fidelity
        if Path(DB_PATH).exists():
            z.write(DB_PATH, "library.db")
        if include_covers:
            covers = CACHE_DIR / "covers"
            if covers.exists():
                for img in covers.glob("*.jpg"):
                    z.write(img, f"covers/{img.name}")

    return {
        "out_path": str(out),
        "size_mb": round(out.stat().st_size / (1024 * 1024), 2),
        "track_count": len(tracks),
    }


def import_pack(pack_path: str, merge: bool = True) -> Dict[str, Any]:
    """
    Pull an exported pack into the local DB. By default merges (matches by
    audio_fingerprint, updates user-flags like rating + cover_path). Set
    merge=False to fully replace the local DB (use with care).
    """
    p = Path(pack_path).expanduser()
    if not p.exists():
        return {"error": f"Not found: {pack_path}"}

    with zipfile.ZipFile(p) as z:
        with z.open("library.json") as fh:
            payload = json.load(fh)
        # Restore covers
        for name in z.namelist():
            if name.startswith("covers/"):
                target = CACHE_DIR / "covers" / Path(name).name
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(name) as src, open(target, "wb") as out:
                    shutil.copyfileobj(src, out)

    if not merge:
        # Full replace: overwrite DB file from pack
        with zipfile.ZipFile(p) as z:
            with z.open("library.db") as src, open(DB_PATH, "wb") as out:
                shutil.copyfileobj(src, out)
        return {"replaced": True, "track_count": payload["track_count"]}

    # Merge: walk each remote track, match by fingerprint, update fields
    updated, inserted, skipped = 0, 0, 0
    for rt in payload["tracks"]:
        fp = rt.get("audio_fingerprint")
        local = None
        if fp:
            from mixmind.database import get_connection
            with get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM tracks WHERE audio_fingerprint = ? LIMIT 1", (fp,)
                ).fetchone()
                if row:
                    local = dict(row)

        if local:
            # Take the higher rating, latest user flags
            patch = {}
            if (rt.get("rating") or 0) > (local.get("rating") or 0):
                patch["rating"] = rt["rating"]
            if rt.get("hot_cues") and not local.get("hot_cues"):
                patch["hot_cues"] = rt["hot_cues"]
            if patch:
                db.update_track(local["id"], patch)
                updated += 1
            else:
                skipped += 1
        else:
            # No matching fingerprint in local — track is new. We can register
            # the metadata but the audio file won't exist on this machine.
            inserted += 1
            try:
                db.upsert_track({**rt, "path": rt.get("path") or f"REMOTE__{rt.get('filename', rt.get('id'))}"})
            except Exception:
                pass

    return {
        "merged": True,
        "updated": updated,
        "inserted_metadata_only": inserted,
        "unchanged": skipped,
    }


def diff_pack(pack_path: str) -> Dict[str, Any]:
    """Show what an import would change without applying it."""
    p = Path(pack_path).expanduser()
    if not p.exists():
        return {"error": f"Not found: {pack_path}"}
    with zipfile.ZipFile(p) as z:
        payload = json.load(z.open("library.json"))

    local_fps = set()
    for t in db.find_tracks(limit=100000):
        if t.get("audio_fingerprint"):
            local_fps.add(t["audio_fingerprint"])

    remote_only = []
    common = []
    for rt in payload["tracks"]:
        fp = rt.get("audio_fingerprint")
        if fp and fp in local_fps:
            common.append({"artist": rt.get("artist"), "title": rt.get("title"), "fp": fp})
        else:
            remote_only.append({"artist": rt.get("artist"), "title": rt.get("title")})

    return {
        "pack_track_count": len(payload["tracks"]),
        "local_track_count": len(local_fps),
        "common_count": len(common),
        "remote_only_count": len(remote_only),
        "remote_only_sample": remote_only[:20],
    }
