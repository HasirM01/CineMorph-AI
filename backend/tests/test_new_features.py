"""Tests for iteration 2 features: streaming, delete cascade, validations."""
import os
import time
import pytest
import requests

BASE_URL = os.environ['REACT_APP_BACKEND_URL'].rstrip('/')
SESSION_TOKEN = os.environ.get('TEST_SESSION_TOKEN', 'test_session_1780567592367')
H = {"Authorization": f"Bearer {SESSION_TOKEN}"}

MP4 = b"\x00\x00\x00\x20ftypmp42" + b"\x00" * 2048

# Real video for tests that go through the AI pipeline
REAL_VIDEO = '/tmp/cinetest/test10s.mp4'


def _upload(real=False):
    if real and os.path.exists(REAL_VIDEO):
        with open(REAL_VIDEO, 'rb') as f:
            content = f.read()
        files = {"file": ("TEST_movie2_real.mp4", content, "video/mp4")}
    else:
        files = {"file": ("TEST_movie2.mp4", MP4, "video/mp4")}
    r = requests.post(f"{BASE_URL}/api/movies/upload", files=files, headers=H)
    assert r.status_code == 200, r.text
    return r.json()["movie_id"]


def _create_job(mid, target="ta"):
    r = requests.post(f"{BASE_URL}/api/dubbing/create",
                      json={"movie_id": mid, "target_language": target, "cost_approved": True}, headers=H)
    return r


def _wait_completed(jid, timeout=40):
    for _ in range(timeout):
        r = requests.get(f"{BASE_URL}/api/dubbing/{jid}", headers=H)
        if r.json().get("status") == "completed":
            return True
        time.sleep(1)
    return False


# ---- Validation ----
class TestValidations:
    def test_invalid_target_language(self):
        mid = _upload()
        r = _create_job(mid, target="xx")
        assert r.status_code == 400
        assert "Invalid target language" in r.text
        requests.delete(f"{BASE_URL}/api/movies/{mid}", headers=H)

    def test_invalid_file_format_rejected(self):
        files = {"file": ("bad.txt", b"hello", "text/plain")}
        r = requests.post(f"{BASE_URL}/api/movies/upload", files=files, headers=H)
        assert r.status_code == 400


# ---- Stream endpoints ----
class TestStreaming:
    def test_stream_movie_ok(self):
        mid = _upload()
        r = requests.get(f"{BASE_URL}/api/movies/{mid}/stream", headers=H)
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("video/")
        assert len(r.content) > 0
        requests.delete(f"{BASE_URL}/api/movies/{mid}", headers=H)

    def test_stream_movie_unauth(self):
        r = requests.get(f"{BASE_URL}/api/movies/abc/stream")
        assert r.status_code == 401

    def test_stream_movie_not_found(self):
        r = requests.get(f"{BASE_URL}/api/movies/nonexistent_xyz/stream", headers=H)
        assert r.status_code == 404


# ---- Full lifecycle: upload -> dub -> stream/download -> delete cascade ----
class TestLifecycle:
    def test_full_workflow(self):
        mid = _upload(real=True)
        r = _create_job(mid, "ta")
        assert r.status_code == 200, r.text
        jid = r.json()["job_id"]

        assert _wait_completed(jid), "Job didn't complete within timeout"

        # Download
        d = requests.get(f"{BASE_URL}/api/dubbing/{jid}/download", headers=H)
        assert d.status_code == 200, d.text
        assert d.headers.get("content-type", "").startswith("video/")
        assert len(d.content) > 0

        # Stream dubbed
        s = requests.get(f"{BASE_URL}/api/dubbing/{jid}/stream", headers=H)
        assert s.status_code == 200
        assert len(s.content) > 0

        # Delete job
        dj = requests.delete(f"{BASE_URL}/api/dubbing/{jid}", headers=H)
        assert dj.status_code == 200
        # Confirm gone
        g = requests.get(f"{BASE_URL}/api/dubbing/{jid}", headers=H)
        assert g.status_code == 404

        # Delete movie
        dm = requests.delete(f"{BASE_URL}/api/movies/{mid}", headers=H)
        assert dm.status_code == 200
        g2 = requests.get(f"{BASE_URL}/api/movies/{mid}", headers=H)
        assert g2.status_code == 404

    def test_delete_movie_cascades_jobs(self):
        mid = _upload()
        r = _create_job(mid, "hi")
        jid = r.json()["job_id"]
        # Don't wait for completion - delete movie immediately
        time.sleep(2)
        dm = requests.delete(f"{BASE_URL}/api/movies/{mid}", headers=H)
        assert dm.status_code == 200
        # Related job should be gone too
        gj = requests.get(f"{BASE_URL}/api/dubbing/{jid}", headers=H)
        assert gj.status_code == 404


# ---- Delete error handling ----
class TestDeleteErrors:
    def test_delete_nonexistent_movie(self):
        r = requests.delete(f"{BASE_URL}/api/movies/nope_xyz", headers=H)
        assert r.status_code == 404

    def test_delete_nonexistent_job(self):
        r = requests.delete(f"{BASE_URL}/api/dubbing/nope_xyz", headers=H)
        assert r.status_code == 404

    def test_delete_unauth(self):
        r = requests.delete(f"{BASE_URL}/api/movies/anything")
        assert r.status_code == 401
