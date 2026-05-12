"""
Genre classifier.

We use a hybrid approach:
1. If the file has a genre tag, normalize it against a known vocabulary.
2. Otherwise, use a heuristic classifier based on BPM + energy + brightness +
   danceability + feature vector to pick one of the DJ-relevant genres.

This is a rule-based v0.3 — v1.0 will swap in a trained neural model.
"""
from typing import Optional, Dict, Any
import json
import re

# Canonical DJ-oriented genre list
CANONICAL_GENRES = [
    "House",
    "Tech House",
    "Deep House",
    "Progressive House",
    "Techno",
    "Minimal Techno",
    "Trance",
    "Psy Trance",
    "Drum & Bass",
    "Dubstep",
    "Hip-Hop",
    "Trap",
    "R&B",
    "Pop",
    "Disco",
    "Funk",
    "Reggaeton",
    "Afro House",
    "Ambient",
    "Chillout",
    "Breakbeat",
    "Hardstyle",
    "Electro",
    "Future Bass",
]

# Map common tag strings -> canonical
GENRE_ALIASES = {
    r"\btech[\s-]?house\b": "Tech House",
    r"\bdeep[\s-]?house\b": "Deep House",
    r"\bprogressive[\s-]?house\b": "Progressive House",
    r"\bafro[\s-]?house\b": "Afro House",
    r"\bminimal\b": "Minimal Techno",
    r"\btechno\b": "Techno",
    r"\bhouse\b": "House",
    r"\bpsy[\s-]?trance\b": "Psy Trance",
    r"\btrance\b": "Trance",
    r"\bd(&|and|n)b\b": "Drum & Bass",
    r"\bdrum\s*&?\s*bass\b": "Drum & Bass",
    r"\bdubstep\b": "Dubstep",
    r"\bhip[\s-]?hop\b": "Hip-Hop",
    r"\brap\b": "Hip-Hop",
    r"\btrap\b": "Trap",
    r"\br\s*&\s*b\b": "R&B",
    r"\bpop\b": "Pop",
    r"\bdisco\b": "Disco",
    r"\bfunk\b": "Funk",
    r"\breggaeton\b": "Reggaeton",
    r"\bambient\b": "Ambient",
    r"\bchill(out)?\b": "Chillout",
    r"\bbreak[\s-]?beat\b": "Breakbeat",
    r"\bhardstyle\b": "Hardstyle",
    r"\belectro\b": "Electro",
    r"\bfuture\s*bass\b": "Future Bass",
}


def normalize_tag_genre(tag: Optional[str]) -> Optional[str]:
    """Match a user-provided genre tag against canonical vocabulary."""
    if not tag:
        return None
    t = tag.lower().strip()
    for pattern, canonical in GENRE_ALIASES.items():
        if re.search(pattern, t):
            return canonical
    return None


def heuristic_classify(features: Dict[str, Any]) -> str:
    """
    Classify based on BPM + energy + brightness + danceability.
    This is a heuristic — good enough for a starting point, and can be
    refined once you like/dislike enough tracks to train a real model.
    """
    bpm = features.get("bpm") or 0
    energy = features.get("energy") or 0
    brightness = features.get("brightness") or 0.5
    danceability = features.get("danceability") or 0.5

    # BPM-first rough bucket
    if bpm < 85:
        if energy < 3:
            return "Ambient" if brightness < 0.35 else "Chillout"
        if energy < 5:
            return "Hip-Hop"
        return "Trap" if brightness > 0.45 else "R&B"

    if 85 <= bpm < 100:
        if energy < 4:
            return "Chillout"
        if brightness > 0.5:
            return "Hip-Hop"
        return "R&B"

    if 100 <= bpm < 115:
        if energy > 7:
            return "Reggaeton"
        return "Disco" if brightness > 0.55 else "Funk"

    if 115 <= bpm < 122:
        # House territory
        if brightness < 0.35 and energy < 6:
            return "Deep House"
        if energy > 7.5:
            return "Tech House"
        return "House"

    if 122 <= bpm < 128:
        if danceability > 0.7 and energy > 6.5:
            return "Tech House"
        if brightness > 0.55:
            return "Progressive House"
        if energy < 5:
            return "Deep House"
        return "House"

    if 128 <= bpm < 135:
        if energy > 8 and brightness > 0.55:
            return "Techno"
        if energy < 6:
            return "Progressive House"
        if danceability > 0.7:
            return "Tech House"
        return "Techno"

    if 135 <= bpm < 142:
        if energy > 8:
            return "Techno"
        return "Trance"

    if 142 <= bpm < 150:
        if energy > 8:
            return "Psy Trance"
        return "Trance"

    if 150 <= bpm < 160:
        if brightness > 0.55 and energy > 7.5:
            return "Hardstyle"
        return "Dubstep"

    if 160 <= bpm < 180:
        if danceability > 0.6:
            return "Drum & Bass"
        return "Dubstep"

    if bpm >= 180:
        return "Drum & Bass"

    return "Electro"


def classify_track(track: Dict[str, Any]) -> str:
    """
    Classify a track. Prefers tag-based genre if it matches canonical list.
    Falls back to heuristic.
    """
    tag_genre = normalize_tag_genre(track.get("genre_tag"))
    if tag_genre:
        return tag_genre
    return heuristic_classify(track)
