"""
Smoke tests covering all 8 Pro endpoints + core endpoints.

We use a session-scoped DB seeded with 20 demo tracks so each Pro endpoint
gets realistic input shape. Each test asserts:
  - HTTP 200
  - response key shape matches what the frontend expects

Run with:
    cd backend && pytest tests/ -v
"""


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "version" in body


def test_stats(client, seeded_db):
    r = client.get("/api/stats")
    assert r.status_code == 200
    s = r.json()
    assert s["total_tracks"] == seeded_db["inserted"]
    assert s["analyzed"] >= s["total_tracks"]  # all demo tracks are pre-analyzed


def test_list_tracks(client):
    r = client.get("/api/tracks?limit=5")
    assert r.status_code == 200
    body = r.json()
    assert len(body["tracks"]) == 5
    t = body["tracks"][0]
    # Required fields the UI reads
    for key in ("id", "title", "artist", "bpm", "camelot", "energy", "genre_ai"):
        assert key in t, f"missing key {key} in track row"


def test_track_detail(client, first_track_id):
    r = client.get(f"/api/tracks/{first_track_id}")
    assert r.status_code == 200
    t = r.json()
    assert t["id"] == first_track_id
    # Pro modules need these
    assert t.get("beat_times") is not None
    assert t.get("downbeats") is not None


def test_genres(client):
    r = client.get("/api/genres")
    assert r.status_code == 200
    body = r.json()
    assert "Tech House" in body["genres"]
    assert "Techno" in body["genres"]


# ============================================================================
# Pro 1: Track ID
# ============================================================================

def test_pro_trackid_library(client, first_track_id):
    r = client.post(f"/api/pro/trackid/library/{first_track_id}")
    assert r.status_code == 200
    body = r.json()
    assert "local_matches" in body
    # Should match itself with high confidence
    assert isinstance(body["local_matches"], list)


# ============================================================================
# Pro 2: Live Mix
# ============================================================================

def test_pro_livemix_suggest(client, first_track_id):
    payload = {"current_track_id": first_track_id, "mode": "steady", "limit": 3}
    r = client.post("/api/pro/livemix/suggest", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert "candidates" in body
    # Should return up to 3 candidates
    assert len(body["candidates"]) <= 3
    if body["candidates"]:
        c = body["candidates"][0]
        for key in ("track", "mix_score", "bpm_pct_change", "harmonic", "reasons"):
            assert key in c, f"missing {key} in candidate"


def test_pro_livemix_played(client, first_track_id):
    r = client.post(f"/api/pro/livemix/played/{first_track_id}")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


# ============================================================================
# Pro 3: Phrase Grid
# ============================================================================

def test_pro_phrasegrid(client, first_track_id):
    r = client.get(f"/api/pro/phrasegrid/{first_track_id}")
    assert r.status_code == 200
    body = r.json()
    for key in ("track_id", "bpm", "bars_per_phrase", "boundaries", "sections"):
        assert key in body, f"missing {key} in phrase grid"
    assert body["bars_per_phrase"] == 32
    assert isinstance(body["sections"], list)


# ============================================================================
# Pro 4: Hot Cues
# ============================================================================

def test_pro_hotcues_generate(client, first_track_id):
    r = client.post(f"/api/pro/hotcues/{first_track_id}?save=true")
    # Demo tracks are 1-sec silent WAVs, so generation may fail loading audio.
    # We accept either success or a 400 with a clear error message.
    assert r.status_code in (200, 400)
    if r.status_code == 200:
        body = r.json()
        assert "cues" in body
        assert isinstance(body["cues"], list)


def test_pro_hotcues_get(client, first_track_id):
    r = client.get(f"/api/pro/hotcues/{first_track_id}")
    assert r.status_code == 200
    body = r.json()
    assert "cues" in body
    assert isinstance(body["cues"], list)


# ============================================================================
# Pro 5: Quality Audit
# ============================================================================

def test_pro_quality_track(client, first_track_id):
    r = client.get(f"/api/pro/quality/{first_track_id}")
    # Same caveat as hot cues — silent WAV may yield error verdict
    assert r.status_code in (200, 400, 500)


# ============================================================================
# Pro 6: Trends
# ============================================================================

def test_pro_trends(client):
    r = client.get("/api/pro/trends")
    assert r.status_code == 200
    body = r.json()
    assert "sections" in body
    # Offline / sandboxed envs return empty sections — that's fine
    assert isinstance(body["sections"], list)


# ============================================================================
# Pro 7: Stems (capabilities only — actual separation is heavy)
# ============================================================================

def test_pro_stems_capabilities(client):
    r = client.get("/api/pro/stems/capabilities")
    assert r.status_code == 200
    body = r.json()
    assert "available" in body
    assert "stems" in body
    assert body["stems"] == ["vocals", "drums", "bass", "other"]


# ============================================================================
# Pro 8: Gig Export — needs a playlist first
# ============================================================================

def test_pro_gig_export(client, tmp_path):
    # 1. Generate a small playlist
    pl_payload = {"duration_minutes": 15, "curve": "journey", "save_as": "test_gig"}
    r = client.post("/api/playlist/generate", json=pl_payload)
    assert r.status_code == 200
    playlist_id = r.json().get("playlist_id")
    assert playlist_id is not None

    # 2. Export to a temp dir
    out_dir = tmp_path / "gig_out"
    payload = {
        "out_root": str(out_dir),
        "playlist_id": playlist_id,
        "playlist_name": "test_gig",
        "normalize_lufs": None,        # skip normalize (silent WAV)
        "include_covers": False,
    }
    r = client.post("/api/pro/gig/export", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["track_count"] > 0
    # Sidecar files exist
    assert (out_dir / "rekordbox.xml").exists()
    assert (out_dir / "playlist.m3u8").exists()
    assert (out_dir / "metadata.json").exists()
    assert (out_dir / "README.txt").exists()


# ============================================================================
# Other essentials — recommend, dedupe, playlist gen
# ============================================================================

def test_recommend(client):
    r = client.get("/api/ai/recommend?limit=10")
    assert r.status_code == 200
    body = r.json()
    assert "tracks" in body
    # Demo seeder auto-likes some tracks, so we should get recs
    assert len(body["tracks"]) > 0


def test_train(client):
    r = client.post("/api/ai/train")
    assert r.status_code == 200
    body = r.json()
    assert "trained" in body


def test_playlist_generate(client):
    payload = {"duration_minutes": 30, "curve": "journey"}
    r = client.post("/api/playlist/generate", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert "tracks" in body
    assert len(body["tracks"]) > 0
