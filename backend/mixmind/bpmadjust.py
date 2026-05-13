"""
BPM micro-adjust — work out a smooth pitch ramp between two tracks.

If track A is 124 BPM and you want to mix into B at 128 BPM, instead of
slamming +3.2% pitch (which pitches everything up), you can:

  - Start with a small +0.5% bump
  - Each 8 bars increase by another +0.5%
  - Reach the target by the time the outro of A is done

This module computes the exact ramp schedule. Output:

  step_n   from_bpm   to_bpm   start_sec   duration_sec   pitch_%
  1        124.0      124.6    0           7.7            +0.50
  2        124.6      125.3    7.7         7.7            +1.00
  ...
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def plan_bpm_ramp(
    track_a_bpm: float,
    track_b_bpm: float,
    a_outro_start_sec: float,
    a_duration_sec: float,
    bars_per_step: int = 8,
    max_pct_per_step: float = 0.5,
) -> Dict[str, Any]:
    """
    Compute a step-by-step pitch fader ramp on Deck A so its outgoing BPM
    smoothly converges with Deck B's intro.
    """
    if a_outro_start_sec >= a_duration_sec or a_duration_sec <= 0:
        return {"error": "Invalid outro/duration"}

    delta = track_b_bpm - track_a_bpm
    pct = (delta / track_a_bpm) * 100  # pitch fader % needed

    # Bars per step → seconds per step using current BPM
    sec_per_bar = (60.0 / track_a_bpm) * 4
    sec_per_step = sec_per_bar * bars_per_step

    available = a_duration_sec - a_outro_start_sec
    n_steps_max = max(1, int(available / sec_per_step))
    n_steps_needed = max(1, int(abs(pct) / max_pct_per_step))
    n_steps = min(n_steps_max, n_steps_needed)
    pct_per_step = pct / n_steps

    schedule: List[Dict[str, Any]] = []
    cur_bpm = track_a_bpm
    cur_t = a_outro_start_sec
    for i in range(n_steps):
        next_bpm = cur_bpm + (track_a_bpm * pct_per_step / 100)
        schedule.append({
            "step": i + 1,
            "from_bpm": round(cur_bpm, 2),
            "to_bpm": round(next_bpm, 2),
            "start_sec": round(cur_t, 2),
            "duration_sec": round(sec_per_step, 2),
            "pitch_pct_total": round(((i + 1) * pct_per_step), 2),
        })
        cur_bpm = next_bpm
        cur_t += sec_per_step

    return {
        "track_a_bpm": track_a_bpm,
        "track_b_bpm": track_b_bpm,
        "total_pitch_pct": round(pct, 2),
        "n_steps": n_steps,
        "schedule": schedule,
        "advice": _advice(pct, n_steps),
    }


def _advice(pct: float, n_steps: int) -> str:
    if abs(pct) < 1:
        return "Negligible — just slam it."
    if abs(pct) < 3:
        return f"Comfortable {n_steps}-step ramp; audience won't notice."
    if abs(pct) < 5:
        return "Aggressive — consider a longer outro or a transitional break."
    return "Too far. Pick a different next track or use a tool track between them."
