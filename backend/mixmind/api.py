"""FastAPI Web API for MixMind DJ."""
import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

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

# v0.5 — extended pro modules
from mixmind import autotag, coverart, vibetags, similarity, settracks
from mixmind import sethistory, djmimic, b2b, highlight, bpmadjust
from mixmind import samples, mastering, venues, styleanalysis, cloudsync, newrelease

# v0.6 — vocal identification
from mixmind import vocalid

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
                        # Vocal ID — auto-tag gender during initial analysis
                        try:
                            vocal = vocalid.analyze_vocal(track["path"])
                            if "error" not in vocal:
                                for k in ("vocal_presence", "vocal_gender", "vocal_f0_hz",
                                          "vocal_confidence", "vocal_f0_lo", "vocal_f0_hi"):
                                    if k in vocal:
                                        result[k] = vocal[k]
                        except Exception:
                            pass
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




# ============================================================================
# v0.5 Pro Modules (13 extended capabilities)
# ============================================================================

# --- 1. Auto-tag / organize -------------------------------------------------

class AutoTagPlanIn(BaseModel):
    out_root: str
    track_ids: Optional[List[int]] = None


@app.post("/api/pro/autotag/plan")
def pro_autotag_plan(body: AutoTagPlanIn):
    return {"plan": autotag.plan_organization(body.out_root, body.track_ids)}


class AutoTagExecuteIn(BaseModel):
    out_root: str
    track_ids: Optional[List[int]] = None
    mode: str = "copy"   # copy | move
    update_paths: bool = False


@app.post("/api/pro/autotag/execute")
def pro_autotag_execute(body: AutoTagExecuteIn):
    return autotag.execute_organization(
        body.out_root, body.track_ids, body.mode, body.update_paths
    )


# --- 2. Cover art ----------------------------------------------------------

class CoverIn(BaseModel):
    track_ids: Optional[List[int]] = None
    online: bool = True


@app.post("/api/pro/coverart/run")
def pro_cover_run(body: CoverIn):
    return coverart.autocomplete_covers(body.track_ids, body.online)


@app.get("/api/pro/coverart/{track_id}")
def pro_cover_for_track(track_id: int):
    t = db.get_track(track_id)
    if not t:
        raise HTTPException(404)
    cp = t.get("cover_path")
    if not cp or not os.path.exists(cp):
        raise HTTPException(404, "No cover")
    return FileResponse(cp, media_type="image/jpeg")


# --- 3. Vibe tags ----------------------------------------------------------

class VibeRunIn(BaseModel):
    track_ids: Optional[List[int]] = None


@app.post("/api/pro/vibe/tag")
def pro_vibe_tag(body: VibeRunIn):
    return vibetags.tag_library(body.track_ids)


@app.get("/api/pro/vibe/find")
def pro_vibe_find(
    mood: Optional[str] = None,
    texture: Optional[str] = None,
    time: Optional[str] = None,
    element: Optional[str] = None,
    bpm_min: Optional[float] = None,
    bpm_max: Optional[float] = None,
    limit: int = 50,
):
    return {"tracks": vibetags.find_by_vibe(mood, texture, time, element, bpm_min, bpm_max, limit)}


# --- 4. Sonic similarity ---------------------------------------------------

@app.get("/api/pro/similarity/{track_id}")
def pro_similarity(
    track_id: int,
    limit: int = 30,
    same_genre_only: bool = False,
    bpm_window: Optional[float] = None,
):
    return {"tracks": similarity.find_sonic_neighbors(track_id, limit, same_genre_only, bpm_window)}


# --- 5. Set tracklist recovery ---------------------------------------------

class TracklistIn(BaseModel):
    set_path: str
    window_sec: float = 30.0
    step_sec: float = 15.0
    min_confidence: float = 0.20


@app.post("/api/pro/tracklist/recover")
def pro_tracklist_recover(body: TracklistIn):
    return settracks.recover_tracklist(body.set_path, body.window_sec, body.step_sec, body.min_confidence)


class TracklistFormatIn(BaseModel):
    tracklist: Dict[str, Any]
    format: str = "text"      # text | 1001tracklists


@app.post("/api/pro/tracklist/format")
def pro_tracklist_format(body: TracklistFormatIn):
    if body.format == "1001tracklists":
        return {"text": settracks.format_as_1001tracklists(body.tracklist)}
    return {"text": settracks.format_as_text(body.tracklist)}


# --- 6. Set history --------------------------------------------------------

class RecordSetIn(BaseModel):
    name: str
    tracklist: Dict[str, Any]
    venue: Optional[str] = None
    notes: Optional[str] = None


@app.post("/api/pro/sethistory/record")
def pro_history_record(body: RecordSetIn):
    set_id = sethistory.record_set(body.name, body.tracklist, body.venue, body.notes)
    return {"set_id": set_id}


@app.get("/api/pro/sethistory")
def pro_history_list(limit: int = 100):
    return {"sets": sethistory.get_history(limit)}


@app.get("/api/pro/sethistory/{set_id}")
def pro_history_get(set_id: int):
    s = sethistory.get_set(set_id)
    if not s:
        raise HTTPException(404)
    return s


@app.get("/api/pro/sethistory/profile")
def pro_history_profile(since_days: Optional[int] = None):
    return sethistory.style_profile(since_days)


@app.get("/api/pro/sethistory/drift")
def pro_history_drift():
    return sethistory.style_drift()


# --- 7. DJ mimic -----------------------------------------------------------

class MimicFingerprintIn(BaseModel):
    tracks: List[Dict[str, Any]]


@app.post("/api/pro/mimic/fingerprint")
def pro_mimic_fingerprint(body: MimicFingerprintIn):
    return djmimic.fingerprint_reference(body.tracks)


class MimicGenerateIn(BaseModel):
    fingerprint: Dict[str, Any]
    target_count: Optional[int] = None


@app.post("/api/pro/mimic/generate")
def pro_mimic_generate(body: MimicGenerateIn):
    return {"tracks": djmimic.generate_mimic_setlist(body.fingerprint, body.target_count)}


# --- 8. B2B compatibility --------------------------------------------------

class B2BCompareIn(BaseModel):
    your_ids: List[int]
    partner_meta: List[Dict[str, Any]]


@app.post("/api/pro/b2b/compare")
def pro_b2b_compare(body: B2BCompareIn):
    return b2b.compare_libraries(body.your_ids, body.partner_meta)


class B2BSetlistIn(BaseModel):
    your_ids: List[int]
    partner_meta: List[Dict[str, Any]]
    duration_minutes: int = 60


@app.post("/api/pro/b2b/setlist")
def pro_b2b_setlist(body: B2BSetlistIn):
    return {"tracks": b2b.b2b_setlist(body.your_ids, body.partner_meta, body.duration_minutes)}


# --- 9. Highlight reel -----------------------------------------------------

class HighlightFindIn(BaseModel):
    set_path: str
    clip_seconds: float = 30.0
    n_top: int = 1


@app.post("/api/pro/highlight/find")
def pro_highlight_find(body: HighlightFindIn):
    return highlight.find_highlight(body.set_path, body.clip_seconds, body.n_top)


class HighlightExportIn(BaseModel):
    set_path: str
    out_path: str
    start_sec: float
    duration_sec: float = 30.0


@app.post("/api/pro/highlight/export")
def pro_highlight_export(body: HighlightExportIn):
    out = highlight.export_clip(body.set_path, body.out_path, body.start_sec, body.duration_sec)
    return {"output": out}


# --- 10. BPM adjust --------------------------------------------------------

class BPMRampIn(BaseModel):
    track_a_bpm: float
    track_b_bpm: float
    a_outro_start_sec: float
    a_duration_sec: float
    bars_per_step: int = 8


@app.post("/api/pro/bpmadjust/ramp")
def pro_bpm_ramp(body: BPMRampIn):
    return bpmadjust.plan_bpm_ramp(
        body.track_a_bpm, body.track_b_bpm,
        body.a_outro_start_sec, body.a_duration_sec, body.bars_per_step
    )


# --- 11. Sample / acapella library ----------------------------------------

class SampleScanIn(BaseModel):
    folder: str


@app.post("/api/pro/samples/scan")
def pro_samples_scan(body: SampleScanIn):
    return samples.scan_sample_folder(body.folder)


@app.get("/api/pro/samples/find")
def pro_samples_find(
    sample_type: Optional[str] = None,
    bpm_min: Optional[float] = None,
    bpm_max: Optional[float] = None,
    camelot: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 50,
):
    return {"samples": samples.find_samples(sample_type, bpm_min, bpm_max, camelot, query, limit)}


# --- 12. Mastering / Platinum-Notes equivalent -----------------------------

class MasterIn(BaseModel):
    track_ids: List[int]
    out_dir: str
    target_lufs: float = -8.0


@app.post("/api/pro/mastering/batch")
def pro_master_batch(body: MasterIn):
    return mastering.batch_master(body.track_ids, body.out_dir, body.target_lufs)


# --- 13. Venue profiles ----------------------------------------------------

@app.get("/api/pro/venues")
def pro_venues_list():
    return {"venues": venues.list_venues()}


class VenueSetlistIn(BaseModel):
    venue_id: str
    duration_minutes: int = 60


@app.post("/api/pro/venues/setlist")
def pro_venue_setlist(body: VenueSetlistIn):
    return {"tracks": venues.setlist_for_venue(body.venue_id, body.duration_minutes)}


# --- 14. Style analysis ----------------------------------------------------

@app.get("/api/pro/styleanalysis/{track_id}")
def pro_style_analysis(track_id: int):
    return styleanalysis.analyze_track_sections(track_id)


# --- 15. Cloud sync --------------------------------------------------------

class CloudExportIn(BaseModel):
    out_path: str
    include_covers: bool = True


@app.post("/api/pro/cloud/export")
def pro_cloud_export(body: CloudExportIn):
    return cloudsync.export_pack(body.out_path, body.include_covers)


class CloudImportIn(BaseModel):
    pack_path: str
    merge: bool = True


@app.post("/api/pro/cloud/import")
def pro_cloud_import(body: CloudImportIn):
    return cloudsync.import_pack(body.pack_path, body.merge)


@app.post("/api/pro/cloud/diff")
def pro_cloud_diff(body: CloudImportIn):
    return cloudsync.diff_pack(body.pack_path)


# --- 16. New-release monitor -----------------------------------------------

@app.get("/api/pro/releases/subscriptions")
def pro_release_subscriptions():
    return {"subscriptions": newrelease.list_subscriptions()}


class SubscribeIn(BaseModel):
    name: str
    kind: str = "artist"
    source: str = "beatport"


@app.post("/api/pro/releases/subscribe")
def pro_release_subscribe(body: SubscribeIn):
    sid = newrelease.add_subscription(body.name, body.kind, body.source)
    return {"id": sid}


@app.delete("/api/pro/releases/subscribe/{sub_id}")
def pro_release_unsubscribe(sub_id: int):
    newrelease.remove_subscription(sub_id)
    return {"ok": True}


@app.post("/api/pro/releases/auto")
def pro_release_auto():
    return newrelease.auto_subscribe_from_library()


@app.post("/api/pro/releases/check")
def pro_release_check():
    return newrelease.check_all()


@app.get("/api/pro/releases/feed")
def pro_release_feed(unseen_only: bool = True, limit: int = 100):
    return {"releases": newrelease.feed(unseen_only, limit)}




# ============================================================================
# v0.6 — Vocal identification
# ============================================================================


class VocalAnalyzeIn(BaseModel):
    track_ids: Optional[List[int]] = None
    refine_sample_type: bool = True


@app.post("/api/pro/vocal/analyze")
def pro_vocal_analyze(body: VocalAnalyzeIn):
    """Run vocal-presence + gender ID across the library."""
    return vocalid.analyze_library(body.track_ids, body.refine_sample_type)


@app.get("/api/pro/vocal/track/{track_id}")
def pro_vocal_for_track(track_id: int):
    """Re-analyze a single track without writing to DB."""
    t = db.get_track(track_id)
    if not t:
        raise HTTPException(404)
    return vocalid.analyze_vocal(t["path"])


@app.get("/api/pro/vocal/find")
def pro_vocal_find(
    gender: Optional[str] = None,
    bpm_min: Optional[float] = None,
    bpm_max: Optional[float] = None,
    camelot: Optional[str] = None,
    sample_type: Optional[str] = None,
    min_presence: float = 0.10,
    limit: int = 100,
):
    """Find vocal-male / vocal-female / mixed / instrumental tracks."""
    return {
        "tracks": vocalid.find_vocals(
            gender=gender, bpm_min=bpm_min, bpm_max=bpm_max,
            camelot=camelot, sample_type=sample_type,
            min_presence=min_presence, limit=limit,
        )
    }
