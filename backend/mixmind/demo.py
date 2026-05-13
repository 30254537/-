"""
Demo data seeder.

Generates 60 realistic synthetic tracks across the genres a working
DJ actually plays — Tech House, Deep House, House, Techno, Trance,
Drum & Bass, Hip-Hop, Trap. Every track gets:

  - Plausible BPM for its genre (with some intra-genre variance)
  - A real Camelot key (drawn evenly across the wheel)
  - Energy, brightness, danceability values that match the genre
  - Real LUFS / true-peak figures
  - Beat times + downbeats consistent with the BPM
  - Structure cue points (intro/drop/breakdown/outro) that are
    plausible for a 5-7 minute extended mix
  - 24-dim feature vector (random Gaussian, but reproducible per track)
  - 3-band waveform envelope (low/mid/high) for UI rendering
  - Audio fingerprint computed off the feature vector

This lets users explore the entire Pro Tools UI immediately —
recommendations, playlists, hot cues, phrase grid, quality audit,
trend radar — without needing to scan their own music yet.

Important: this is *demo* data. Tracks marked with `is_demo=1` in
the path so they can be cleaned up easily. Generated audio files
are 1-second silent .wav stubs so file streaming UI links don't 404.
"""
from __future__ import annotations

import json
import random
import struct
import wave
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from mixmind import database as db
from mixmind.config import CACHE_DIR


# ---------------------------------------------------------------------------
# Genre-aware track templates
# ---------------------------------------------------------------------------

@dataclass
class GenreTemplate:
    name: str
    bpm_range: Tuple[int, int]
    energy_range: Tuple[float, float]
    brightness_range: Tuple[float, float]
    danceability_range: Tuple[float, float]
    typical_loudness: float


GENRES = [
    GenreTemplate("Tech House",       (122, 128), (6.5, 8.5), (0.45, 0.65), (0.75, 0.92), -7.5),
    GenreTemplate("Deep House",       (118, 124), (4.5, 6.5), (0.30, 0.50), (0.65, 0.85), -8.5),
    GenreTemplate("House",            (120, 126), (5.5, 7.5), (0.40, 0.60), (0.70, 0.90), -7.8),
    GenreTemplate("Progressive House",(126, 132), (6.0, 8.0), (0.50, 0.70), (0.65, 0.85), -7.0),
    GenreTemplate("Techno",           (128, 138), (7.5, 9.5), (0.50, 0.75), (0.75, 0.92), -7.0),
    GenreTemplate("Minimal Techno",   (124, 130), (5.0, 7.0), (0.35, 0.55), (0.70, 0.88), -8.0),
    GenreTemplate("Trance",           (132, 140), (7.0, 9.0), (0.55, 0.75), (0.65, 0.85), -7.2),
    GenreTemplate("Drum & Bass",      (170, 178), (8.0, 9.5), (0.60, 0.80), (0.70, 0.90), -6.8),
    GenreTemplate("Hip-Hop",          (85, 100),  (5.0, 7.0), (0.40, 0.60), (0.55, 0.75), -8.2),
    GenreTemplate("Trap",             (140, 156), (6.5, 8.5), (0.50, 0.70), (0.55, 0.78), -7.5),
]

# Realistic sample artist names per genre
ARTISTS = {
    "Tech House":        ["Fisher", "Chris Lake", "Dom Dolla", "James Hype", "Cloonee", "Vintage Culture", "Wade", "Solardo"],
    "Deep House":        ["Lane 8", "Tinlicker", "Yotto", "Massane", "Le Youth", "Cassian", "Nick Warren"],
    "House":             ["MK", "Gorgon City", "Disclosure", "Duke Dumont", "CamelPhat", "Patrick Topping"],
    "Progressive House": ["Eric Prydz", "deadmau5", "Cristoph", "Sasha", "Mha Iri", "Anyma"],
    "Techno":            ["Charlotte de Witte", "Amelie Lens", "Adam Beyer", "Reinier Zonneveld", "Pan-Pol", "ANNA"],
    "Minimal Techno":    ["Ricardo Villalobos", "Loco Dice", "Hot Since 82", "Solomun", "Apollonia"],
    "Trance":            ["Above & Beyond", "ARTY", "Cosmic Gate", "Markus Schulz", "Aly & Fila"],
    "Drum & Bass":       ["Sub Focus", "Wilkinson", "Dimension", "Andy C", "Chase & Status", "Hybrid Minds"],
    "Hip-Hop":           ["J. Cole", "Kendrick Lamar", "Drake", "21 Savage", "Travis Scott", "Future"],
    "Trap":              ["RL Grime", "Flosstradamus", "Carnage", "Baauer", "TroyBoi", "Ekali"],
}

# Track title templates — varied so playlists feel real
TITLE_TEMPLATES = [
    "Midnight {n}", "{n} Dreams", "Echoes of {n}", "{n} Ritual", "Lost in {n}",
    "{n} Pulse", "Beyond {n}", "{n} Theory", "The {n} Effect", "{n} Frequency",
    "Stranger {n}", "Above {n}", "{n} Mirage", "Synthetic {n}", "{n} Horizon",
    "Forever {n}", "{n} Symphony", "Dancing in {n}", "{n} Code", "Voyager {n}",
]
TITLE_NOUNS = ["Tokyo", "Berlin", "Ibiza", "Neon", "Voltage", "Stardust", "Phoenix",
               "Velvet", "Mercury", "Solar", "Phantom", "Cosmos", "Echo", "Prism",
               "Gravity", "Nebula", "Vertex", "Mirage", "Pulse", "Onyx"]
SUFFIXES = ["", " (Original Mix)", " (Extended Mix)", " (Club Mix)", " (Original Mix)"]


# Camelot wheel — 12 keys × 2 modes
CAMELOT_KEYS = [f"{n}{m}" for n in range(1, 13) for m in ("A", "B")]

KEY_NAMES = {
    "1A": ("Abm", "G#m"), "1B": "B",
    "2A": ("Ebm", "D#m"), "2B": "F#",
    "3A": "Bbm",          "3B": "Db",
    "4A": "Fm",           "4B": "Ab",
    "5A": "Cm",           "5B": "Eb",
    "6A": "Gm",           "6B": "Bb",
    "7A": "Dm",           "7B": "F",
    "8A": "Am",           "8B": "C",
    "9A": "Em",           "9B": "G",
    "10A": "Bm",          "10B": "D",
    "11A": ("F#m", "Gbm"),"11B": "A",
    "12A": ("C#m", "Dbm"),"12B": "E",
}


def _key_for_camelot(camelot: str) -> str:
    v = KEY_NAMES.get(camelot, "Am")
    return v[0] if isinstance(v, tuple) else v


def _mood_from_energy(energy: float) -> str:
    if energy < 3:
        return "chill"
    if energy < 5:
        return "warmup"
    if energy < 7:
        return "groove"
    if energy < 9:
        return "peak"
    return "intense"


# ---------------------------------------------------------------------------
# Synthesis helpers
# ---------------------------------------------------------------------------

def _gen_beat_grid(bpm: float, duration: float) -> Tuple[List[float], List[float]]:
    """Return (beat_times, downbeats) for a steady 4/4 grid."""
    beat_period = 60.0 / bpm
    beats = []
    t = 0.0
    while t < duration:
        beats.append(round(t, 3))
        t += beat_period
    # Every 4th beat is a downbeat (4/4)
    downbeats = beats[::4]
    return beats, downbeats


def _gen_structure(duration: float, bpm: float) -> Dict[str, float]:
    """Plausible structural cue points for a 5-7 min extended mix."""
    # Snap each cue to the nearest 16-bar boundary
    bar = (60.0 / bpm) * 4
    phrase = bar * 16  # 16 bars per phrase

    intro_end_bars = 32  # 32 bars of intro
    intro_end = intro_end_bars * bar
    first_drop = intro_end                                  # drop right after intro
    breakdown = first_drop + phrase * 2                     # 32 bars after drop
    outro_start = duration - phrase * 2                     # last 32 bars
    return {
        "intro_end": round(intro_end, 2),
        "first_drop": round(first_drop, 2),
        "breakdown": round(breakdown, 2),
        "outro_start": round(max(outro_start, breakdown + phrase), 2),
    }


def _gen_waveform(duration: float, energy: float, bpm: float, points: int = 300) -> List[List[float]]:
    """Synthesize a 3-band envelope shaped by energy + a kick on every beat."""
    bands = []
    beat_period = 60.0 / bpm
    for i in range(points):
        t = (i / points) * duration
        # Kick pulse on each beat
        beat_phase = (t % beat_period) / beat_period
        kick = max(0.0, 1.0 - beat_phase * 5) ** 2  # decays after onset

        # Section weighting — louder mids in drop, quiet in breakdown
        if t < duration * 0.1:
            section_gain = 0.4
        elif t > duration * 0.85:
            section_gain = 0.5
        elif duration * 0.45 < t < duration * 0.6:  # breakdown
            section_gain = 0.45
        else:
            section_gain = 1.0

        norm_energy = energy / 10.0
        low = round(min(1.0, (kick * 0.7 + 0.3) * norm_energy * section_gain), 3)
        mid = round(min(1.0, (0.4 + random.random() * 0.4) * norm_energy * section_gain), 3)
        high = round(min(1.0, (0.3 + random.random() * 0.3) * norm_energy * section_gain), 3)
        bands.append([low, mid, high])
    return bands


def _gen_feature_vector(genre: str, bpm: float, energy: float) -> List[float]:
    """24-dim feature vector. Reproducible per genre by seeding from genre name."""
    rng = random.Random(hash(genre) ^ int(bpm * 100) ^ int(energy * 100))
    # MFCC-ish (13)
    vec = [round(rng.gauss(0, 30), 5) for _ in range(13)]
    # 3 top chroma values
    vec += [round(rng.uniform(0, 1), 5) for _ in range(3)]
    # mean chroma
    vec.append(round(rng.uniform(0.2, 0.6), 5))
    # spectral centroid (Hz)
    vec.append(round(rng.uniform(1500, 5500), 5))
    # rolloff (Hz)
    vec.append(round(rng.uniform(3000, 9000), 5))
    # bandwidth
    vec.append(round(rng.uniform(1000, 4000), 5))
    # contrast
    vec.append(round(rng.uniform(15, 45), 5))
    # zcr
    vec.append(round(rng.uniform(0.05, 0.20), 5))
    # spectral flatness
    vec.append(round(rng.uniform(0.01, 0.20), 5))
    # centroid std
    vec.append(round(rng.uniform(200, 1500), 5))
    return vec


def _audio_fingerprint(features: List[float]) -> str:
    import hashlib
    rounded = [round(f, 2) for f in features[:16]]
    payload = ",".join(str(x) for x in rounded)
    return hashlib.md5(payload.encode()).hexdigest()[:16]


def _write_silent_wav(path: Path, duration: float = 1.0, sr: int = 22050):
    """Write a 1-second silent WAV stub so audio streaming endpoints don't 404."""
    n_samples = int(duration * sr)
    with wave.open(str(path), "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(b"\x00\x00" * n_samples)


# ---------------------------------------------------------------------------
# Public seeder
# ---------------------------------------------------------------------------

def seed_demo_library(count: int = 60, audio_dir: Path | None = None) -> Dict[str, Any]:
    """
    Insert `count` synthetic tracks into the database. Returns a summary.
    """
    db.init_db()

    if audio_dir is None:
        audio_dir = CACHE_DIR / "demo_audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    inserted = 0
    skipped = 0
    samples_per_genre = max(1, count // len(GENRES))
    rng = random.Random(42)
    now = datetime.utcnow().isoformat()

    for genre in GENRES:
        for i in range(samples_per_genre):
            artist = rng.choice(ARTISTS[genre.name])
            noun = rng.choice(TITLE_NOUNS)
            title_base = rng.choice(TITLE_TEMPLATES).format(n=noun)
            title = title_base + rng.choice(SUFFIXES)

            bpm = round(rng.uniform(*genre.bpm_range), 2)
            camelot = rng.choice(CAMELOT_KEYS)
            energy = round(rng.uniform(*genre.energy_range), 2)
            brightness = round(rng.uniform(*genre.brightness_range), 3)
            danceability = round(rng.uniform(*genre.danceability_range), 3)
            duration = round(rng.uniform(290, 410), 2)        # 4'50" - 6'50"
            loudness = round(genre.typical_loudness + rng.gauss(0, 0.6), 2)
            true_peak = round(rng.uniform(-1.5, -0.1), 2)

            beats, downbeats = _gen_beat_grid(bpm, duration)
            struct_pts = _gen_structure(duration, bpm)
            waveform = _gen_waveform(duration, energy, bpm)
            features = _gen_feature_vector(genre.name, bpm, energy)
            fp = _audio_fingerprint(features)

            # Mark path with is_demo so it's identifiable
            safe_artist = artist.replace(" ", "_").replace("&", "and")
            safe_title = "".join(c for c in title if c.isalnum() or c in "._- ").strip()
            filename = f"DEMO__{safe_artist}__{safe_title}.wav"
            wav_path = audio_dir / filename
            if not wav_path.exists():
                _write_silent_wav(wav_path)

            # Skip if already present
            existing = db.get_track_by_path(str(wav_path))
            if existing:
                skipped += 1
                continue

            row: Dict[str, Any] = {
                "path": str(wav_path),
                "filename": filename,
                "filesize": wav_path.stat().st_size,
                "duration": duration,
                "title": title,
                "artist": artist,
                "album": f"{genre.name} Vol. {rng.randint(1, 12)}",
                "genre_tag": genre.name,
                "year": rng.randint(2020, 2026),

                "bpm": bpm,
                "bpm_confidence": round(rng.uniform(0.78, 0.96), 3),
                "key_name": _key_for_camelot(camelot),
                "camelot": camelot,
                "key_confidence": round(rng.uniform(0.65, 0.92), 3),
                "energy": energy,
                "loudness": loudness,
                "true_peak": true_peak,
                "danceability": danceability,
                "brightness": brightness,

                "beat_times": json.dumps(beats),
                "downbeats": json.dumps(downbeats),
                "intro_end": struct_pts["intro_end"],
                "first_drop": struct_pts["first_drop"],
                "breakdown": struct_pts["breakdown"],
                "outro_start": struct_pts["outro_start"],
                "waveform_bands": json.dumps(waveform),
                "peak_start": struct_pts["first_drop"],
                "peak_end": round(struct_pts["first_drop"] + 30, 2),

                "genre_ai": genre.name,
                "mood_label": _mood_from_energy(energy),
                "feature_vector": json.dumps(features),
                "audio_fingerprint": fp,

                "rating": 0,
                "play_count": 0,
                "scanned_at": now,
                "analyzed_at": now,
            }
            db.upsert_track(row)
            inserted += 1

    # Auto-tag vibes for the seeded tracks
    try:
        from mixmind import vibetags
        vibetags.tag_library()
    except Exception:
        pass

    # Auto-rate a handful as "liked" so AI recs work right away
    rated = 0
    if inserted > 0:
        all_tracks = db.find_tracks(limit=10000)
        liked_sample = rng.sample(all_tracks, min(8, len(all_tracks)))
        for tr in liked_sample:
            db.set_rating(tr["id"], 1)
            rated += 1

    return {
        "inserted": inserted,
        "skipped_existing": skipped,
        "auto_liked": rated,
        "audio_dir": str(audio_dir),
        "total_in_library": db.count_tracks(),
    }


def clear_demo_library() -> Dict[str, Any]:
    """Remove every track whose filename starts with DEMO__."""
    from mixmind.database import get_connection
    with get_connection() as conn:
        cur = conn.execute("SELECT COUNT(*) FROM tracks WHERE filename LIKE 'DEMO__%'")
        before = cur.fetchone()[0]
        conn.execute("DELETE FROM tracks WHERE filename LIKE 'DEMO__%'")
    return {"deleted": before}
