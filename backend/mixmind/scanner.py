"""Scan filesystem for audio files and extract metadata tags."""
from pathlib import Path
from typing import Iterator, Dict, Any, Optional
import os

from mutagen import File as MutagenFile
from mutagen.id3 import ID3NoHeaderError

from mixmind.config import AUDIO_EXTENSIONS


def iter_audio_files(root: str) -> Iterator[Path]:
    """Yield all audio files under root recursively."""
    root_path = Path(root)
    if not root_path.exists():
        raise FileNotFoundError(f"Path does not exist: {root}")
    if root_path.is_file():
        if root_path.suffix.lower() in AUDIO_EXTENSIONS:
            yield root_path
        return
    for dirpath, _, filenames in os.walk(root_path):
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix.lower() in AUDIO_EXTENSIONS:
                yield p


def extract_tags(path: Path) -> Dict[str, Any]:
    """Extract ID3/tag metadata from an audio file."""
    info: Dict[str, Any] = {
        "path": str(path.resolve()),
        "filename": path.name,
        "filesize": path.stat().st_size,
        "title": None,
        "artist": None,
        "album": None,
        "genre_tag": None,
        "year": None,
        "duration": None,
    }

    try:
        audio = MutagenFile(str(path), easy=True)
    except (ID3NoHeaderError, Exception):
        audio = None

    if audio is None:
        # Fallback: parse filename "Artist - Title.mp3"
        stem = path.stem
        if " - " in stem:
            parts = stem.split(" - ", 1)
            info["artist"] = parts[0].strip()
            info["title"] = parts[1].strip()
        else:
            info["title"] = stem
        return info

    def _first(key: str) -> Optional[str]:
        v = audio.get(key)
        if v and isinstance(v, list):
            return str(v[0]) if v else None
        return str(v) if v else None

    info["title"] = _first("title")
    info["artist"] = _first("artist")
    info["album"] = _first("album")
    info["genre_tag"] = _first("genre")
    year_raw = _first("date") or _first("year")
    if year_raw:
        try:
            info["year"] = int(str(year_raw)[:4])
        except ValueError:
            pass

    # Duration from file info
    if hasattr(audio, "info") and hasattr(audio.info, "length"):
        info["duration"] = float(audio.info.length)

    # Fallback artist/title from filename if tags missing
    if not info["title"] or not info["artist"]:
        stem = path.stem
        if " - " in stem:
            parts = stem.split(" - ", 1)
            if not info["artist"]:
                info["artist"] = parts[0].strip()
            if not info["title"]:
                info["title"] = parts[1].strip()
        else:
            if not info["title"]:
                info["title"] = stem

    return info
