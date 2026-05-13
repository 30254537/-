"""
Cover art helpers.

Two modes:
  - extract: pull embedded album art from MP3/FLAC/M4A/etc. into JPEG files
  - fetch:   for tracks missing art, look up MusicBrainz / iTunes / Discogs
             (online, optional) and embed the result back into the file

Both modes update a `cover_path` column on the track record so the UI can
display thumbnails immediately.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from mixmind import database as db
from mixmind.config import CACHE_DIR


COVER_DIR = CACHE_DIR / "covers"
COVER_DIR.mkdir(parents=True, exist_ok=True)


def extract_cover(track: Dict[str, Any]) -> Optional[str]:
    """Extract embedded cover into COVER_DIR/<id>.jpg. Return path or None."""
    src = track.get("path")
    if not src or not os.path.exists(src):
        return None
    dest = COVER_DIR / f"{track['id']}.jpg"
    try:
        from mutagen import File as MutagenFile
        from mutagen.id3 import APIC
        f = MutagenFile(src)
        if f is None:
            return None
        # ID3
        if f.tags is not None:
            for k, v in f.tags.items():
                if isinstance(v, APIC):
                    dest.write_bytes(v.data)
                    return str(dest)
        # MP4
        if hasattr(f, "tags") and f.tags is not None:
            covr = f.tags.get("covr") if hasattr(f.tags, "get") else None
            if covr:
                dest.write_bytes(bytes(covr[0]))
                return str(dest)
        # FLAC / Vorbis
        pics = getattr(f, "pictures", None)
        if pics:
            dest.write_bytes(pics[0].data)
            return str(dest)
    except Exception:
        return None
    return None


def fetch_cover_online(artist: str, title: str) -> Optional[bytes]:
    """Try MusicBrainz cover-art-archive then iTunes Search API."""
    try:
        import requests
    except ImportError:
        return None
    if not artist or not title:
        return None

    # 1. iTunes Search (fast, no key required)
    try:
        r = requests.get(
            "https://itunes.apple.com/search",
            params={"term": f"{artist} {title}", "entity": "song", "limit": 1},
            timeout=8,
        )
        if r.status_code == 200:
            data = r.json()
            results = data.get("results") or []
            if results:
                url = results[0].get("artworkUrl100", "").replace("100x100", "600x600")
                if url:
                    img = requests.get(url, timeout=8)
                    if img.status_code == 200 and img.content:
                        return img.content
    except Exception:
        pass

    # 2. MusicBrainz / Cover Art Archive (slower, no key)
    try:
        r = requests.get(
            "https://musicbrainz.org/ws/2/recording",
            params={"query": f'artist:"{artist}" AND recording:"{title}"', "fmt": "json", "limit": 1},
            headers={"User-Agent": "MixMindDJ/0.5 (https://github.com/mixmind)"},
            timeout=8,
        )
        if r.status_code == 200:
            data = r.json()
            recs = data.get("recordings") or []
            for rec in recs:
                for rel in rec.get("releases", []):
                    rid = rel.get("id")
                    if not rid:
                        continue
                    img = requests.get(f"https://coverartarchive.org/release/{rid}/front-500", timeout=8)
                    if img.status_code == 200:
                        return img.content
                    break
    except Exception:
        pass
    return None


def embed_cover_in_file(track_path: str, jpeg_bytes: bytes) -> bool:
    """Write jpeg_bytes back into the file's tags."""
    try:
        from mutagen import File as MutagenFile
        from mutagen.id3 import ID3, APIC
        from mutagen.flac import Picture, FLAC
        from mutagen.mp4 import MP4Cover, MP4

        ext = Path(track_path).suffix.lower()
        if ext == ".mp3":
            try:
                tags = ID3(track_path)
            except Exception:
                tags = ID3()
            tags.delall("APIC")
            tags.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=jpeg_bytes))
            tags.save(track_path)
            return True
        if ext == ".flac":
            f = FLAC(track_path)
            f.clear_pictures()
            pic = Picture()
            pic.type = 3
            pic.mime = "image/jpeg"
            pic.data = jpeg_bytes
            f.add_picture(pic)
            f.save()
            return True
        if ext in (".m4a", ".mp4"):
            f = MP4(track_path)
            f.tags["covr"] = [MP4Cover(jpeg_bytes, imageformat=MP4Cover.FORMAT_JPEG)]
            f.save()
            return True
    except Exception:
        return False
    return False


def autocomplete_covers(track_ids: Optional[List[int]] = None,
                       online: bool = True) -> Dict[str, Any]:
    """For every track without cover art, extract or fetch one."""
    if track_ids:
        tracks = [t for t in (db.get_track(tid) for tid in track_ids) if t]
    else:
        tracks = db.find_tracks(limit=100000)

    extracted = 0
    fetched = 0
    failed = 0
    for t in tracks:
        if t.get("cover_path") and Path(t["cover_path"]).exists():
            continue
        cover_path = extract_cover(t)
        if cover_path:
            db.update_track(t["id"], {"cover_path": cover_path})
            extracted += 1
            continue
        if not online:
            failed += 1
            continue
        artist = t.get("artist") or ""
        title = t.get("title") or ""
        img = fetch_cover_online(artist, title)
        if img:
            dest = COVER_DIR / f"{t['id']}.jpg"
            dest.write_bytes(img)
            db.update_track(t["id"], {"cover_path": str(dest)})
            # Also embed into file (best effort)
            embed_cover_in_file(t["path"], img)
            fetched += 1
        else:
            failed += 1

    return {
        "extracted": extracted,
        "fetched": fetched,
        "failed": failed,
        "total_processed": extracted + fetched + failed,
    }
