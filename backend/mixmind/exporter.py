"""
DJ software interoperability exporters.

Currently supported:
  - Rekordbox XML (Pioneer DJ rekordbox import format)
  - M3U8 (universal, works in Serato and most players)

Rekordbox XML format spec:
https://cdn.rekordbox.com/files/20200410160904/xml_format_list.pdf
"""
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape
from xml.dom.minidom import parseString
from typing import List, Dict, Any, Optional
import json

from mixmind import __version__


def _file_uri(path: str) -> str:
    """
    Convert an absolute filesystem path to the file:// URI format Rekordbox expects.
    Windows: file://localhost/D:/Music/track.mp3
    macOS/Linux: file://localhost/Music/track.mp3
    """
    p_str = str(path).replace("\\", "/")
    # Detect Windows-style path like "D:/..." — do NOT call .resolve() because
    # on a non-Windows host it would mistakenly prepend the cwd.
    if len(p_str) > 2 and p_str[1] == ":":
        parts = "/" + p_str
    else:
        try:
            parts = Path(p_str).resolve().as_posix()
        except Exception:
            parts = p_str
    encoded = quote(parts, safe="/:")
    return f"file://localhost{encoded}"


# Rekordbox Tonality code:  A=Am, B=Bm etc with sharps/flats normalized
_KEY_NAME_REKORDBOX = {
    # major
    "C": "C",   "Db": "Db",  "D": "D",   "Eb": "Eb",
    "E": "E",   "F": "F",    "F#": "Gb", "G": "G",
    "Ab": "Ab", "A": "A",    "Bb": "Bb", "B": "B",
    # minor
    "Cm": "Cm",   "C#m": "Dbm", "Dm": "Dm",   "D#m": "Ebm",
    "Em": "Em",   "Fm": "Fm",   "F#m": "Gbm", "Gm": "Gm",
    "G#m": "Abm", "Am": "Am",   "Bbm": "Bbm", "Bm": "Bm",
}


def _track_xml(track: Dict[str, Any], track_id: int) -> str:
    """Generate <TRACK> XML for one track."""
    attrs = []

    def A(k: str, v: Any):
        if v is None or v == "":
            return
        attrs.append(f'{k}="{escape(str(v), {chr(34): "&quot;"})}"')

    A("TrackID", track_id)
    A("Name", track.get("title") or track.get("filename") or "")
    A("Artist", track.get("artist") or "")
    A("Album", track.get("album") or "")
    A("Genre", track.get("genre_ai") or track.get("genre_tag") or "")
    if track.get("duration"):
        A("TotalTime", int(track["duration"]))
    if track.get("bpm"):
        A("AverageBpm", f"{track['bpm']:.2f}")
    key = track.get("key_name")
    if key:
        A("Tonality", _KEY_NAME_REKORDBOX.get(key, key))
    if track.get("loudness") is not None:
        # Rekordbox "DateAdded" ignored; loudness in comments
        pass
    if track.get("rating") is not None:
        # Rekordbox uses 0/51/102/153/204/255 scale
        rating_map = {-1: 0, 0: 0, 1: 153, 2: 255}
        A("Rating", rating_map.get(track["rating"], 0))
    if track.get("path"):
        A("Location", _file_uri(track["path"]))
    if track.get("filesize"):
        A("Size", track["filesize"])

    opening = "<TRACK " + " ".join(attrs)

    # POSITION_MARK cues from structural analysis
    cue_points: List[str] = []
    cue_idx = 0

    def _cue(num: int, name: str, start: float, color: str = "0xFF69B4"):
        nonlocal cue_idx
        return (
            f'<POSITION_MARK Name="{escape(name)}" Type="0" '
            f'Start="{start:.3f}" Num="{num}"/>'
        )

    if track.get("intro_end"):
        cue_points.append(_cue(0, "Intro End", float(track["intro_end"])))
    if track.get("first_drop"):
        cue_points.append(_cue(1, "Drop", float(track["first_drop"])))
    if track.get("breakdown"):
        cue_points.append(_cue(2, "Breakdown", float(track["breakdown"])))
    if track.get("outro_start"):
        cue_points.append(_cue(3, "Outro", float(track["outro_start"])))

    # If pro 8-slot hot cues exist, replace structural cues with them
    hot = track.get("hot_cues")
    if hot:
        try:
            hot_list = json.loads(hot) if isinstance(hot, str) else hot
            if hot_list:
                cue_points = []
                for c in hot_list[:8]:
                    cue_points.append(
                        f'<POSITION_MARK Name="{escape(c.get("name") or "Cue")}" '
                        f'Type="0" Start="{float(c.get("time_sec", 0)):.3f}" '
                        f'Num="{int(c.get("slot", 0))}"/>'
                    )
        except Exception:
            pass

    # TEMPO (beatgrid)
    tempo_xml = ""
    bpm = track.get("bpm")
    downbeats_json = track.get("downbeats")
    if bpm and downbeats_json:
        try:
            downbeats = json.loads(downbeats_json) if isinstance(downbeats_json, str) else downbeats_json
            if downbeats:
                tempo_xml = (
                    f'<TEMPO Inizio="{downbeats[0]:.3f}" Bpm="{bpm:.2f}" '
                    f'Metro="4/4" Battito="1"/>'
                )
        except Exception:
            pass

    inner = tempo_xml + "".join(cue_points)
    if inner:
        return opening + ">" + inner + "</TRACK>"
    return opening + "/>"


def export_rekordbox_xml(
    tracks: List[Dict[str, Any]],
    out_path: str,
    playlists: Optional[Dict[str, List[int]]] = None,
) -> str:
    """
    Export tracks and optional playlists to a Rekordbox-compatible XML file.
    Import in Rekordbox via: Preferences -> Advanced -> rekordbox xml.
    """
    collection_tracks = []
    id_to_local = {}
    for i, t in enumerate(tracks, 1):
        id_to_local[t["id"]] = i
        collection_tracks.append(_track_xml(t, i))

    collection = (
        f'<COLLECTION Entries="{len(tracks)}">'
        + "".join(collection_tracks)
        + "</COLLECTION>"
    )

    # Playlists — folder containing one NODE per playlist
    playlists = playlists or {}
    playlist_nodes = []
    for name, track_ids in playlists.items():
        entries = "".join(
            f'<TRACK Key="{id_to_local[tid]}"/>'
            for tid in track_ids if tid in id_to_local
        )
        playlist_nodes.append(
            f'<NODE Name="{escape(name)}" Type="1" KeyType="0" '
            f'Entries="{len(track_ids)}">{entries}</NODE>'
        )

    root_playlist = (
        '<PLAYLISTS>'
        '<NODE Type="0" Name="ROOT" Count="{c}">'
        '<NODE Name="MixMind DJ" Type="0" Count="{c}">'
        '{nodes}'
        '</NODE>'
        '</NODE>'
        '</PLAYLISTS>'
    ).format(c=len(playlists), nodes="".join(playlist_nodes))

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<DJ_PLAYLISTS Version="1.0.0">'
        f'<PRODUCT Name="MixMind DJ" Version="{__version__}" Company="MixMind"/>'
        f'{collection}'
        f'{root_playlist}'
        '</DJ_PLAYLISTS>'
    )

    # Pretty-print
    pretty = parseString(xml).toprettyxml(indent="  ", encoding="UTF-8")
    Path(out_path).write_bytes(pretty)
    return out_path


def export_serato_crate(tracks: List[Dict[str, Any]], out_path: str) -> str:
    """
    Minimal Serato .crate export. Serato crates are a binary format; we emit
    a .txt playlist that Serato can import via File -> Import Playlist.
    For full binary crate support see the roadmap (v0.5).
    """
    lines = ["# Serato import-compatible playlist"]
    for t in tracks:
        lines.append(t["path"])
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")
    return out_path
