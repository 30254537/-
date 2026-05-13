"""Shared pytest fixtures — isolated DB + demo data per test session."""
import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def _isolated_data_dir(tmp_path_factory):
    """Point MixMind at a throwaway data dir so we don't trample the user's library."""
    tmp = tmp_path_factory.mktemp("mixmind-test-data")
    os.environ["MIXMIND_DATA_DIR"] = str(tmp)
    # Force re-import of config so DB_PATH points to the new dir
    import importlib
    import mixmind.config
    importlib.reload(mixmind.config)
    import mixmind.database
    importlib.reload(mixmind.database)
    yield tmp


@pytest.fixture(scope="session")
def seeded_db(_isolated_data_dir):
    """Seed the demo library once per session."""
    from mixmind.demo import seed_demo_library
    summary = seed_demo_library(count=20)   # 20 is plenty for tests
    return summary


@pytest.fixture()
def client(seeded_db):
    """FastAPI TestClient, isolated DB pre-seeded."""
    from fastapi.testclient import TestClient
    from mixmind.api import app
    return TestClient(app)


@pytest.fixture()
def first_track_id(client):
    r = client.get("/api/tracks?limit=1")
    assert r.status_code == 200
    data = r.json()
    assert data["tracks"], "no tracks in seeded DB"
    return data["tracks"][0]["id"]
