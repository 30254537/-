"""Configuration and paths."""
from pathlib import Path
import os

# Data directory - stores SQLite DB, ML models, cache
DATA_DIR = Path(os.environ.get("MIXMIND_DATA_DIR", Path.home() / ".mixmind"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "library.db"
MODEL_PATH = DATA_DIR / "preference_model.joblib"
CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Supported audio file extensions
AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".aiff", ".aif", ".m4a", ".ogg", ".wma"}

# Audio analysis settings
SAMPLE_RATE = 22050  # Downsample for analysis speed
ANALYSIS_DURATION = 120  # Only analyze first N seconds for speed (None = full track)
HOP_LENGTH = 512

# BPM detection range
BPM_MIN = 60
BPM_MAX = 200

# Energy thresholds (0-10 scale)
ENERGY_LEVELS = {
    "chill": (0, 3),
    "warmup": (3, 5),
    "groove": (5, 7),
    "peak": (7, 9),
    "intense": (9, 10),
}

# Camelot wheel mapping (standard key -> Camelot notation)
CAMELOT_MAP = {
    "C": "8B", "Am": "8A",
    "G": "9B", "Em": "9A",
    "D": "10B", "Bm": "10A",
    "A": "11B", "F#m": "11A",
    "E": "12B", "C#m": "12A",
    "B": "1B", "G#m": "1A",
    "F#": "2B", "D#m": "2A",
    "Db": "3B", "Bbm": "3A",
    "Ab": "4B", "Fm": "4A",
    "Eb": "5B", "Cm": "5A",
    "Bb": "6B", "Gm": "6A",
    "F": "7B", "Dm": "7A",
}

# Krumhansl key profiles
KRUMHANSL_MAJOR = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
KRUMHANSL_MINOR = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
