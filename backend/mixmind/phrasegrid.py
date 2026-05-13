"""
Phrase Grid — 32-bar / 16-bar / 8-bar structural grid for mixing.

DJ tracks (especially House / Techno / Trance / DnB / Tech House) are
written in **phrases** — multiples of 8 bars that align with section
changes. Mix-in / mix-out points only sound natural when they land on
phrase boundaries.

This module:

  * Reads the existing beat grid + downbeats from the analyzer
  * Aligns to true downbeats (4-beat bar)
  * Marks 8-bar, 16-bar, 32-bar boundaries (color-coded for the UI)
  * Detects the "best" mix-in points (32-bar boundary close to intro_end)
  * Detects the "best" mix-out points (32-bar boundary close to outro_start)

Output is consumed by both the Phrase Grid view and Live Mix Assistant.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

from mixmind import database as db


@dataclass
class PhraseBoundary:
    time_sec: float
    bar: int                # bar number from start of track (1-indexed)
    type: str               # "8" | "16" | "32" — strongest grouping it falls on
    label: Optional[str] = None


@dataclass
class PhraseGrid:
    track_id: int
    bpm: Optional[float]
    bars_per_phrase: int                 # 32 by default
    total_bars: int
    boundaries: List[PhraseBoundary]
    sections: List[Dict[str, Any]]       # sequential phrase sections with energy
    mix_in_points: List[float]
    mix_out_points: List[float]


def _energy_for_section(start: float, end: float, beat_times: List[float]) -> float:
    """Approximate per-section relative energy via beat density."""
    if end <= start:
        return 0.0
    in_section = [t for t in beat_times if start <= t < end]
    return round(len(in_section) / max(1.0, end - start), 3)


def build_phrase_grid(track_id: int, bars_per_phrase: int = 32) -> Optional[Dict[str, Any]]:
    track = db.get_track(track_id)
    if not track:
        return None

    beat_times_raw = track.get("beat_times")
    downbeats_raw = track.get("downbeats")
    if not beat_times_raw:
        return None
    try:
        beats = json.loads(beat_times_raw) if isinstance(beat_times_raw, str) else beat_times_raw
        downbeats = json.loads(downbeats_raw) if isinstance(downbeats_raw, str) else (downbeats_raw or [])
    except (TypeError, ValueError):
        return None

    if len(beats) < 16:
        return None

    # If we don't have explicit downbeats, infer every 4th beat is a bar
    if not downbeats:
        downbeats = beats[::4]

    bars = downbeats
    boundaries: List[PhraseBoundary] = []
    for i, t in enumerate(bars):
        bar_num = i + 1
        if bar_num % bars_per_phrase == 1 and bar_num > 1:
            boundaries.append(PhraseBoundary(time_sec=round(float(t), 3), bar=bar_num, type="32",
                                              label=f"Phrase {bar_num // bars_per_phrase + 1}"))
        elif bar_num % 16 == 1 and bar_num > 1:
            boundaries.append(PhraseBoundary(time_sec=round(float(t), 3), bar=bar_num, type="16"))
        elif bar_num % 8 == 1 and bar_num > 1:
            boundaries.append(PhraseBoundary(time_sec=round(float(t), 3), bar=bar_num, type="8"))

    # Sections between consecutive 32-bar boundaries (or 16 if track is short)
    section_step = bars_per_phrase if len(bars) >= bars_per_phrase * 2 else 16
    sections: List[Dict[str, Any]] = []
    for i in range(0, len(bars), section_step):
        start = float(bars[i])
        end = float(bars[i + section_step]) if i + section_step < len(bars) else float(track.get("duration") or beats[-1])
        sections.append({
            "start_sec": round(start, 3),
            "end_sec": round(end, 3),
            "bar_start": i + 1,
            "bar_end": min(i + section_step, len(bars)),
            "energy_density": _energy_for_section(start, end, beats),
            "label": _classify_section(start, end, track),
        })

    # Best mix-in / mix-out: closest 32-bar boundary to intro_end / outro_start
    intro_end = track.get("intro_end")
    outro_start = track.get("outro_start")
    mix_in_points = []
    mix_out_points = []
    boundary_times_32 = [b.time_sec for b in boundaries if b.type == "32"]
    if not boundary_times_32:
        boundary_times_32 = [b.time_sec for b in boundaries if b.type == "16"]

    if intro_end and boundary_times_32:
        # Pick 1-3 closest 32-bar boundaries near intro_end
        sorted_b = sorted(boundary_times_32, key=lambda t: abs(t - intro_end))
        mix_in_points = [round(t, 3) for t in sorted_b[:3]]
    if outro_start and boundary_times_32:
        sorted_b = sorted(boundary_times_32, key=lambda t: abs(t - outro_start))
        mix_out_points = [round(t, 3) for t in sorted_b[:3]]

    grid = PhraseGrid(
        track_id=track_id,
        bpm=track.get("bpm"),
        bars_per_phrase=bars_per_phrase,
        total_bars=len(bars),
        boundaries=boundaries,
        sections=sections,
        mix_in_points=mix_in_points,
        mix_out_points=mix_out_points,
    )

    return {
        "track_id": grid.track_id,
        "bpm": grid.bpm,
        "bars_per_phrase": grid.bars_per_phrase,
        "total_bars": grid.total_bars,
        "boundaries": [asdict(b) for b in grid.boundaries],
        "sections": grid.sections,
        "mix_in_points": grid.mix_in_points,
        "mix_out_points": grid.mix_out_points,
    }


def _classify_section(start: float, end: float, track: Dict[str, Any]) -> str:
    """Tag a section as intro / drop / breakdown / outro / verse based on cues."""
    intro_end = track.get("intro_end") or 0
    first_drop = track.get("first_drop") or 0
    breakdown = track.get("breakdown") or 0
    outro_start = track.get("outro_start") or 0
    duration = track.get("duration") or end

    mid = (start + end) / 2
    if mid < intro_end:
        return "intro"
    if outro_start and mid >= outro_start:
        return "outro"
    if breakdown and abs(mid - breakdown) < (end - start):
        return "breakdown"
    if first_drop and start <= first_drop <= end:
        return "drop"
    if duration and mid > duration * 0.75:
        return "outro_lead"
    return "main"
