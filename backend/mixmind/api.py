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
