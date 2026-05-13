"""FastAPI Web API for MixMind DJ."""
import json
import os
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from mixmind import __version__
from mixmind import database as db
from mixmind.scanner import iter_audio_files, extract_tags
from mixmind.analyzer import analyze_file
from mixmind.classifier import classify_track
from mixmind.dedupe import find_duplicates
from mixmind.preferences import (
    train_preference_model,
    recommend as ai_recommend,
    find_similar,
)
from mixmind.playlist import generate_setlist, export_m3u8
from mixmind.exporter import export_rekordbox_xml
from mixmind.trackid import identify_track
from mixmind.livemix import suggest_next, mark_played
from mixmind.phrasegrid import build_phrase_grid
from mixmind.stems import get_capabilities as stems_capabilities, separate as stems_separate
from mixmind.gigexport import export_gig
from mixmind.trends import get_trend_radar
from mixmind.quality import audit_file, audit_library
from mixmind.hotcues import generate_hot_cues, write_cues_to_db

app = FastAPI(title="MixMind DJ API", version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    db.init_db()


# --- Health & stats ---

@app.get("/api/health")
def health():
    return {"ok": True, "version": __version__}


@app.get("/api/stats")
def stats():
    return db.get_stats()


# --- Tracks ---

@app.get("/api/tracks")
def list_tracks(
    q: Optional[str] = None,
    genre: Optional[str] = None,
    mood: Optional[str] = None,
    bpm_min: Optional[float] = None,
    bpm_max: Optional[float] = None,
    camelot: Optional[str] = None,
    rating: Optional[int] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
):
    tracks = db.find_tracks(
        query=q, genre=genre, mood=mood,
        bpm_min=bpm_min, bpm_max=bpm_max, camelot=camelot, rating=rating,
        limit=limit, offset=offset,
    )
    return {"tracks": tracks, "count": len(tracks)}


@app.get("/api/tracks/{track_id}")
def get_track(track_id: int):
    t = db.get_track(track_id)
    if not t:
        raise HTTPException(404, "Track not found")
    return t


class RatingIn(BaseModel):
    rating: int  # -1, 0, 1, 2


@app.post("/api/tracks/{track_id}/rate")
def rate_track(track_id: int, body: RatingIn):
    if body.rating not in (-1, 0, 1, 2):
        raise HTTPException(400, "Rating must be -1, 0, 1, or 2")
    db.set_rating(track_id, body.rating)
    return {"ok": True}


@app.get("/api/tracks/{track_id}/audio")
def stream_audio(track_id: int):
    t = db.get_track(track_id)
    if not t:
        raise HTTPException(404)
    if not os.path.exists(t["path"]):
        raise HTTPException(404, "File missing on disk")
    return FileResponse(t["path"])


@app.get("/api/tracks/{track_id}/similar")
def similar(track_id: int, limit: int = 20):
    return {"tracks": find_similar(track_id, limit=limit)}


# --- Scan / analyze ---

class ScanIn(BaseModel):
    folder: str
    analyze: bool = True


# In-process job state (simple)
_JOBS: dict = {}


def _run_scan(job_id: str, folder: str, do_analyze: bool):
    try:
        files = list(iter_audio_files(folder))
        _JOBS[job_id] = {"status": "scanning", "total": len(files), "done": 0}
        for fp in files:
            try:
                tags = extract_tags(fp)
                db.upsert_track(tags)
            except Exception:
                pass
            _JOBS[job_id]["done"] += 1

        if do_analyze:
            pending = [t for t in db.find_tracks(limit=100000) if not t.get("bpm")]
            _JOBS[job_id] = {"status": "analyzing", "total": len(pending), "done": 0}
            for track in pending:
                try:
                    result = analyze_file(track["path"])
                    if "error" not in result:
                        merged = {**track, **result}
                        result["genre_ai"] = classify_track(merged)
                        db.update_track(track["id"], result)
                except Exception:
                    pass
                _JOBS[job_id]["done"] += 1

        _JOBS[job_id]["status"] = "done"
    except Exception as e:
        _JOBS[job_id] = {"status": "error", "error": str(e)}


@app.post("/api/scan")
def start_scan(body: ScanIn, bg: BackgroundTasks):
    if not Path(body.folder).exists():
        raise HTTPException(400, "Folder does not exist")
    import uuid
    job_id = uuid.uuid4().hex[:8]
    _JOBS[job_id] = {"status": "starting", "total": 0, "done": 0}
    bg.add_task(_run_scan, job_id, body.folder, body.analyze)
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str):
    if job_id not in _JOBS:
        raise HTTPException(404)
    return _JOBS[job_id]


# --- AI / preferences ---

@app.post("/api/ai/train")
def train():
    return train_preference_model()


@app.get("/api/ai/recommend")
def recommend(limit: int = 20):
    return {"tracks": ai_recommend(limit=limit)}


@app.post("/api/dedupe")
def dedupe():
    n_groups, n_tracks = find_duplicates()
    return {
        "groups": n_groups,
        "tracks": n_tracks,
        "data": db.find_duplicate_groups(),
    }


# --- Playlists ---

class PlaylistIn(BaseModel):
    duration_minutes: int = 60
    curve: str = "journey"
    genre: Optional[str] = None
    bpm_min: Optional[float] = None
    bpm_max: Optional[float] = None
    save_as: Optional[str] = None


@app.post("/api/playlist/generate")
def generate_playlist(body: PlaylistIn):
    bpm_range = (body.bpm_min, body.bpm_max) if (body.bpm_min or body.bpm_max) else None
    setlist = generate_setlist(
        duration_minutes=body.duration_minutes,
        curve=body.curve,
        genre=body.genre,
        bpm_range=bpm_range,
    )
    pid = None
    if body.save_as:
        pid = db.save_playlist(body.save_as, [t["id"] for t in setlist])
    return {"tracks": setlist, "playlist_id": pid}


@app.get("/api/playlists")
def playlists():
    return {"playlists": db.get_playlists()}


@app.get("/api/playlists/{playlist_id}")
def get_playlist(playlist_id: int):
    tracks = db.get_playlist_tracks(playlist_id)
    return {"tracks": tracks}


# --- Genres / moods ---

@app.get("/api/genres")
def genres():
    from mixmind.classifier import CANONICAL_GENRES
    return {"genres": CANONICAL_GENRES}


@app.get("/api/moods")
def moods():
    return {"moods": ["chill", "warmup", "groove", "peak", "intense"]}


# --- Export ---

@app.post("/api/export/rekordbox")
def export_rekordbox(liked_only: bool = False, with_playlists: bool = True):
    """Export library to Rekordbox XML. Returns download path."""
    from mixmind.config import DATA_DIR
    tracks = db.find_tracks(rating=1 if liked_only else None, limit=100000)
    playlists = None
    if with_playlists:
        playlists = {}
        for pl in db.get_playlists():
            pl_tracks = db.get_playlist_tracks(pl["id"])
            playlists[pl["name"]] = [t["id"] for t in pl_tracks]
    out = DATA_DIR / "mixmind_export.xml"
    export_rekordbox_xml(tracks, str(out), playlists=playlists)
    return {"path": str(out), "tracks": len(tracks)}


@app.get("/api/export/download")
def download_export():
    from mixmind.config import DATA_DIR
    path = DATA_DIR / "mixmind_export.xml"
    if not path.exists():
        raise HTTPException(404, "No export available, run /api/export/rekordbox first")
    return FileResponse(str(path), filename="mixmind_rekordbox.xml", media_type="application/xml")


# ============================================================================
# Pro Modules (v0.4)
# ============================================================================

# --- Track ID --------------------------------------------------------------

class TrackIdIn(BaseModel):
    path: str


@app.post("/api/pro/trackid/file")
def pro_trackid_file(body: TrackIdIn):
    """Identify a single audio file by fingerprint match against the library."""
    if not Path(body.path).exists():
        raise HTTPException(400, "File not found")
    return identify_track(body.path)


@app.post("/api/pro/trackid/library/{track_id}")
def pro_trackid_library(track_id: int):
    """Re-identify an existing library track (verifies metadata)."""
    t = db.get_track(track_id)
    if not t:
        raise HTTPException(404)
    return identify_track(t["path"])


# --- Live Mix Assistant ---------------------------------------------------

class LiveMixIn(BaseModel):
    current_track_id: int
    mode: str = "steady"            # steady / build / release
    limit: int = 3


@app.post("/api/pro/livemix/suggest")
def pro_livemix_suggest(body: LiveMixIn):
    return {"candidates": suggest_next(body.current_track_id, mode=body.mode, limit=body.limit)}


@app.post("/api/pro/livemix/played/{track_id}")
def pro_livemix_played(track_id: int):
    mark_played(track_id)
    return {"ok": True}


# --- Phrase Grid -----------------------------------------------------------

@app.get("/api/pro/phrasegrid/{track_id}")
def pro_phrasegrid(track_id: int, bars_per_phrase: int = 32):
    grid = build_phrase_grid(track_id, bars_per_phrase=bars_per_phrase)
    if grid is None:
        raise HTTPException(400, "Phrase grid unavailable. Run analyze first.")
    return grid


# --- AI Stems --------------------------------------------------------------

@app.get("/api/pro/stems/capabilities")
def pro_stems_capabilities():
    return stems_capabilities()


class StemsIn(BaseModel):
    track_id: int
    out_dir: Optional[str] = None


@app.post("/api/pro/stems/separate")
def pro_stems_separate(body: StemsIn):
    t = db.get_track(body.track_id)
    if not t:
        raise HTTPException(404)
    try:
        return stems_separate(t["path"], out_dir=body.out_dir)
    except RuntimeError as e:
        raise HTTPException(400, str(e))


# --- Gig USB Export --------------------------------------------------------

class GigExportIn(BaseModel):
    out_root: str
    playlist_id: Optional[int] = None
    track_ids: Optional[List[int]] = None
    playlist_name: str = "Gig"
    normalize_lufs: Optional[float] = -8.0
    include_covers: bool = True


@app.post("/api/pro/gig/export")
def pro_gig_export(body: GigExportIn):
    try:
        return export_gig(
            out_root=body.out_root,
            track_ids=body.track_ids,
            playlist_id=body.playlist_id,
            playlist_name=body.playlist_name,
            normalize_lufs=body.normalize_lufs,
            include_covers=body.include_covers,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


# --- Trend Radar -----------------------------------------------------------

@app.get("/api/pro/trends")
def pro_trends(genres: Optional[str] = None, refresh: bool = False):
    """genres: comma-separated list e.g. 'Tech House,Techno'."""
    glist = [g.strip() for g in (genres or "").split(",") if g.strip()] or None
    return get_trend_radar(genres=glist, refresh=refresh)


# --- Quality Audit ---------------------------------------------------------

@app.get("/api/pro/quality/{track_id}")
def pro_quality_track(track_id: int):
    t = db.get_track(track_id)
    if not t:
        raise HTTPException(404)
    report = audit_file(t["path"])
    db.update_track(track_id, {
        "quality_verdict": report.get("verdict"),
        "quality_score": report.get("score"),
        "spectral_cutoff_hz": report.get("measured_cutoff_hz"),
    })
    return report


class QualityBatchIn(BaseModel):
    track_ids: Optional[List[int]] = None
    limit: int = 200


@app.post("/api/pro/quality/audit")
def pro_quality_batch(body: QualityBatchIn):
    results = audit_library(track_ids=body.track_ids, limit=body.limit)
    for r in results:
        if "track_id" in r and r.get("verdict") != "error":
            db.update_track(r["track_id"], {
                "quality_verdict": r.get("verdict"),
                "quality_score": r.get("score"),
                "spectral_cutoff_hz": r.get("measured_cutoff_hz"),
            })
    return {"reports": results, "count": len(results)}


# --- Auto Hot Cues ---------------------------------------------------------

@app.post("/api/pro/hotcues/{track_id}")
def pro_hotcues(track_id: int, save: bool = True):
    payload = generate_hot_cues(track_id)
    if "error" in payload:
        raise HTTPException(400, payload["error"])
    if save:
        write_cues_to_db(track_id, payload)
    return payload


@app.get("/api/pro/hotcues/{track_id}")
def pro_hotcues_get(track_id: int):
    t = db.get_track(track_id)
    if not t:
        raise HTTPException(404)
    cues = t.get("hot_cues")
    if not cues:
        return {"track_id": track_id, "cues": []}
    import json as _json
    try:
        return {"track_id": track_id, "cues": _json.loads(cues) if isinstance(cues, str) else cues}
    except Exception:
        return {"track_id": track_id, "cues": []}
