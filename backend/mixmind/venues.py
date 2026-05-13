"""
Venue profiles — different gig types call for different sets.

Define profiles like:
  Beach (Day Party)  — Deep House, 118-122 BPM, energy 5-7
  Club (Peak)        — Tech House / Techno, 124-130 BPM, energy 7-9
  Festival           — Big-room House / Trance, 126-132, energy 8-10
  After Hours        — Minimal Techno, 122-126, energy 4-6
  Bar / Lounge       — Disco / Deep House, 110-120, energy 3-6

Generates a setlist tuned to the venue.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from mixmind import database as db
from mixmind.playlist import generate_setlist


VENUE_PROFILES: Dict[str, Dict[str, Any]] = {
    "beach": {
        "name": "Beach / Day Party",
        "genres": ["Deep House", "House", "Afro House", "Disco"],
        "bpm_min": 116, "bpm_max": 124,
        "energy_min": 4, "energy_max": 7,
        "curve": "warmup",
    },
    "club_peak": {
        "name": "Club — Peak Time",
        "genres": ["Tech House", "Techno", "House"],
        "bpm_min": 124, "bpm_max": 130,
        "energy_min": 7, "energy_max": 10,
        "curve": "peak-time",
    },
    "festival": {
        "name": "Festival Main Stage",
        "genres": ["House", "Progressive House", "Tech House", "Trance"],
        "bpm_min": 126, "bpm_max": 134,
        "energy_min": 7, "energy_max": 10,
        "curve": "festival",
    },
    "afterhours": {
        "name": "After Hours",
        "genres": ["Minimal Techno", "Techno", "Deep House"],
        "bpm_min": 122, "bpm_max": 128,
        "energy_min": 4, "energy_max": 7,
        "curve": "after-hours",
    },
    "bar_lounge": {
        "name": "Bar / Lounge",
        "genres": ["Deep House", "Disco", "Funk", "Chillout"],
        "bpm_min": 105, "bpm_max": 120,
        "energy_min": 3, "energy_max": 6,
        "curve": "warmup",
    },
    "warmup": {
        "name": "Warmup Set",
        "genres": ["Deep House", "House", "Tech House"],
        "bpm_min": 118, "bpm_max": 124,
        "energy_min": 4, "energy_max": 7,
        "curve": "warmup",
    },
    "closing": {
        "name": "Closing Set",
        "genres": ["Deep House", "Minimal Techno", "Ambient"],
        "bpm_min": 110, "bpm_max": 124,
        "energy_min": 3, "energy_max": 6,
        "curve": "after-hours",
    },
}


def list_venues() -> List[Dict[str, Any]]:
    return [{"id": k, **v} for k, v in VENUE_PROFILES.items()]


def setlist_for_venue(venue_id: str, duration_minutes: int = 60) -> List[Dict[str, Any]]:
    profile = VENUE_PROFILES.get(venue_id)
    if not profile:
        return []

    # Try each preferred genre and pick the best-stocked one
    chosen_genre = None
    for g in profile["genres"]:
        n = len(db.find_tracks(genre=g, bpm_min=profile["bpm_min"], bpm_max=profile["bpm_max"], limit=200))
        if n >= 8:
            chosen_genre = g
            break

    return generate_setlist(
        duration_minutes=duration_minutes,
        curve=profile["curve"],
        genre=chosen_genre,
        bpm_range=(profile["bpm_min"], profile["bpm_max"]),
    )
