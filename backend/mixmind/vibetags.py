"""
AI Vibe / Mood multi-dimensional tagging.

Goes beyond "chill / peak / intense" with 4 axes professional DJs use:

  Mood:    dark · euphoric · melancholic · uplifting · neutral
  Texture: driving · groovy · hypnotic · ethereal · funky
  Time:    sunset · late_night · sunrise · daytime · anytime
  Element: vocal · instrumental · acid · classic · modern

The classifier uses the same features the analyzer already computed:
brightness, danceability, BPM, energy, spectral statistics from the
feature_vector. No new audio reads needed — we run over the analyzed
library and write 4 new columns.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from mixmind import database as db


def classify_vibes(track: Dict[str, Any]) -> Dict[str, str]:
    """Return {mood, texture, time, element} for a track."""
    bpm = float(track.get("bpm") or 120)
    energy = float(track.get("energy") or 5)
    brightness = float(track.get("brightness") or 0.5)
    dance = float(track.get("danceability") or 0.5)
    genre = (track.get("genre_ai") or "").lower()

    # Pull spectral stats from feature_vector
    fv = track.get("feature_vector")
    centroid = 3000.0
    flatness = 0.1
    if fv:
        try:
            v = json.loads(fv) if isinstance(fv, str) else fv
            # See compute_feature_vector — index 17 is centroid mean, 22 is flatness
            if len(v) >= 23:
                centroid = float(v[17])
                flatness = float(v[22])
        except Exception:
            pass

    # ── Mood ──────────────────────────────────────────────
    if brightness < 0.40 and energy >= 6.5:
        mood = "dark"
    elif brightness >= 0.60 and energy >= 7.0:
        mood = "euphoric"
    elif brightness < 0.45 and energy < 5:
        mood = "melancholic"
    elif brightness >= 0.55 and energy >= 5 and bpm < 130:
        mood = "uplifting"
    else:
        mood = "neutral"

    # ── Texture ───────────────────────────────────────────
    if dance >= 0.80 and energy >= 6:
        texture = "driving"
    elif dance >= 0.70 and 0.45 <= brightness <= 0.65:
        texture = "groovy"
    elif energy < 5.5 and flatness > 0.08:
        texture = "hypnotic"
    elif brightness >= 0.65 and energy < 6:
        texture = "ethereal"
    elif "funk" in genre or "disco" in genre:
        texture = "funky"
    else:
        texture = "groovy"

    # ── Time of day ───────────────────────────────────────
    if energy >= 8 and bpm >= 128:
        time = "late_night"
    elif energy >= 6.5 and brightness >= 0.55:
        time = "daytime"
    elif energy < 5 and bpm < 122:
        time = "sunrise" if brightness >= 0.55 else "sunset"
    else:
        time = "anytime"

    # ── Element ───────────────────────────────────────────
    # Use spectral centroid: vocal-heavy tracks have stronger 1-3kHz energy
    if 2000 <= centroid <= 4500 and dance < 0.85:
        element = "vocal"
    elif "acid" in genre or "303" in (track.get("title") or "").lower():
        element = "acid"
    elif int(track.get("year") or 2024) < 2010:
        element = "classic"
    elif dance >= 0.80 and brightness > 0.55:
        element = "modern"
    else:
        element = "instrumental"

    return {
        "vibe_mood": mood,
        "vibe_texture": texture,
        "vibe_time": time,
        "vibe_element": element,
    }


def tag_library(track_ids: Optional[List[int]] = None) -> Dict[str, Any]:
    """Run vibe classification across the library, persist columns."""
    if track_ids:
        tracks = [t for t in (db.get_track(tid) for tid in track_ids) if t]
    else:
        tracks = db.get_analyzed_tracks()

    counts: Dict[str, Dict[str, int]] = {
        "mood": {}, "texture": {}, "time": {}, "element": {}
    }
    tagged = 0
    for t in tracks:
        vibes = classify_vibes(t)
        db.update_track(t["id"], vibes)
        counts["mood"][vibes["vibe_mood"]] = counts["mood"].get(vibes["vibe_mood"], 0) + 1
        counts["texture"][vibes["vibe_texture"]] = counts["texture"].get(vibes["vibe_texture"], 0) + 1
        counts["time"][vibes["vibe_time"]] = counts["time"].get(vibes["vibe_time"], 0) + 1
        counts["element"][vibes["vibe_element"]] = counts["element"].get(vibes["vibe_element"], 0) + 1
        tagged += 1

    return {"tagged": tagged, "distribution": counts}


def find_by_vibe(
    mood: Optional[str] = None,
    texture: Optional[str] = None,
    time: Optional[str] = None,
    element: Optional[str] = None,
    bpm_min: Optional[float] = None,
    bpm_max: Optional[float] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Find tracks matching any combination of vibe filters."""
    from mixmind.database import get_connection
    sql = "SELECT * FROM tracks WHERE 1=1"
    params: list = []
    if mood:
        sql += " AND vibe_mood = ?"
        params.append(mood)
    if texture:
        sql += " AND vibe_texture = ?"
        params.append(texture)
    if time:
        sql += " AND vibe_time = ?"
        params.append(time)
    if element:
        sql += " AND vibe_element = ?"
        params.append(element)
    if bpm_min:
        sql += " AND bpm >= ?"
        params.append(bpm_min)
    if bpm_max:
        sql += " AND bpm <= ?"
        params.append(bpm_max)
    sql += " ORDER BY energy DESC LIMIT ?"
    params.append(limit)

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
