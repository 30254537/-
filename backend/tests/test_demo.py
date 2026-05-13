"""Tests for the demo seeder itself."""


def test_seed_count(seeded_db):
    # Should have inserted ~20 tracks (10 genres × 2 each)
    assert seeded_db["inserted"] >= 10
    assert seeded_db["auto_liked"] > 0


def test_seed_tracks_are_analyzed(client, seeded_db):
    r = client.get("/api/tracks?limit=100")
    tracks = r.json()["tracks"]
    for t in tracks:
        assert t["bpm"] is not None
        assert t["camelot"] is not None
        assert t["energy"] is not None
        assert t["genre_ai"] is not None
        assert t["mood_label"] in ("chill", "warmup", "groove", "peak", "intense")


def test_genre_diversity(client):
    r = client.get("/api/stats")
    body = r.json()
    genres = {g["genre_ai"] for g in body["genres"]}
    # Should have at least 5 different genres represented
    assert len(genres) >= 5


def test_camelot_keys_valid(client):
    import re
    r = client.get("/api/tracks?limit=100")
    for t in r.json()["tracks"]:
        assert re.match(r"^\d+[AB]$", t["camelot"]), f"bad camelot {t['camelot']}"


def test_clear_demo(seeded_db):
    from mixmind.demo import clear_demo_library, seed_demo_library
    r = clear_demo_library()
    assert r["deleted"] >= seeded_db["inserted"]
    # Re-seed for other tests in this session
    seed_demo_library(count=20)
