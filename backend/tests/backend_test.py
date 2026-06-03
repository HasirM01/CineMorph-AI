"""Backend API tests for CineMorph AI"""
import os
import io
import time
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://voicecinema-1.preview.emergentagent.com').rstrip('/')
SESSION_TOKEN = os.environ.get('TEST_SESSION_TOKEN', 'test_session_1780481765993')


@pytest.fixture(scope="session")
def auth_headers():
    return {"Authorization": f"Bearer {SESSION_TOKEN}"}


# ---------- Auth ----------
class TestAuth:
    def test_auth_me_unauthenticated(self):
        r = requests.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 401

    def test_auth_me_authenticated(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert "user_id" in data and "email" in data and "name" in data
        assert "_id" not in data

    def test_auth_invalid_token(self):
        r = requests.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": "Bearer invalid_xyz"})
        assert r.status_code == 401


# ---------- Languages ----------
class TestLanguages:
    def test_languages_list(self):
        r = requests.get(f"{BASE_URL}/api/languages")
        assert r.status_code == 200
        langs = r.json()
        assert isinstance(langs, list) and len(langs) >= 15
        codes = [l["code"] for l in langs]
        for c in ["ta", "te", "ml", "kn"]:
            assert c in codes


# ---------- Movies ----------
class TestMovies:
    def test_movies_list_authenticated(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/movies", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_movies_list_unauthenticated(self):
        r = requests.get(f"{BASE_URL}/api/movies")
        assert r.status_code == 401

    def test_upload_invalid_format(self, auth_headers):
        files = {"file": ("test.txt", b"hello world", "text/plain")}
        r = requests.post(f"{BASE_URL}/api/movies/upload", files=files, headers=auth_headers)
        assert r.status_code == 400

    def test_upload_valid_mp4_and_verify_persistence(self, auth_headers):
        # Minimal mp4-like content (just bytes saved as mp4)
        content = b"\x00\x00\x00\x20ftypmp42" + b"\x00" * 1024
        files = {"file": ("TEST_movie.mp4", content, "video/mp4")}
        r = requests.post(f"{BASE_URL}/api/movies/upload", files=files, headers=auth_headers)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["format"] == "mp4"
        assert data["detected_language"] == "en"
        assert "movie_id" in data
        assert "_id" not in data
        # Verify via GET
        mid = data["movie_id"]
        g = requests.get(f"{BASE_URL}/api/movies/{mid}", headers=auth_headers)
        assert g.status_code == 200
        assert g.json()["movie_id"] == mid
        pytest.movie_id = mid

    def test_get_movie_not_found(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/movies/nonexistent", headers=auth_headers)
        assert r.status_code == 404


# ---------- Dubbing ----------
class TestDubbing:
    def test_create_dubbing_job(self, auth_headers):
        mid = getattr(pytest, "movie_id", None)
        if not mid:
            pytest.skip("No movie uploaded")
        r = requests.post(
            f"{BASE_URL}/api/dubbing/create",
            json={"movie_id": mid, "target_language": "ta"},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["target_language"] == "ta"
        assert data["status"] == "processing"
        assert "job_id" in data
        assert "_id" not in data
        pytest.job_id = data["job_id"]

    def test_create_dubbing_invalid_movie(self, auth_headers):
        r = requests.post(
            f"{BASE_URL}/api/dubbing/create",
            json={"movie_id": "bogus", "target_language": "ta"},
            headers=auth_headers,
        )
        assert r.status_code == 404

    def test_list_jobs(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/dubbing/jobs", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_job_progresses(self, auth_headers):
        jid = getattr(pytest, "job_id", None)
        if not jid:
            pytest.skip("No job")
        # poll up to 8s; first stage runs at 2s
        prog = 0
        for _ in range(10):
            r = requests.get(f"{BASE_URL}/api/dubbing/{jid}", headers=auth_headers)
            assert r.status_code == 200
            prog = r.json().get("progress", 0)
            if prog > 0:
                break
            time.sleep(1)
        assert prog > 0, "Mock pipeline did not advance"

    def test_download_before_complete(self, auth_headers):
        jid = getattr(pytest, "job_id", None)
        if not jid:
            pytest.skip("No job")
        r = requests.get(f"{BASE_URL}/api/dubbing/{jid}/download", headers=auth_headers, allow_redirects=False)
        # Either 400 (not completed) or 200 (already done)
        assert r.status_code in (200, 400)


# ---------- Analytics ----------
class TestAnalytics:
    def test_user_analytics(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/analytics/user", headers=auth_headers)
        assert r.status_code == 200
        d = r.json()
        for k in ["total_uploads", "total_dubbing_jobs", "completed_jobs", "in_progress_jobs", "failed_jobs", "languages_used"]:
            assert k in d
        assert d["total_uploads"] >= 1
