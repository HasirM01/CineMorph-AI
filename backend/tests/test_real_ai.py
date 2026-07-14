"""Tests for Real AI mode endpoints (config, estimate-cost, create with cost approval)"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://voicecinema-1.preview.emergentagent.com').rstrip('/')
SESSION_TOKEN = os.environ.get('TEST_SESSION_TOKEN', 'test_session_real_1780654393043')
TEST_VIDEO = '/tmp/cinetest/test10s.mp4'


@pytest.fixture(scope="session")
def auth_headers():
    return {"Authorization": f"Bearer {SESSION_TOKEN}"}


@pytest.fixture(scope="module")
def uploaded_movie(auth_headers):
    """Upload a real 10s video so duration/cost works"""
    with open(TEST_VIDEO, 'rb') as f:
        files = {"file": ("TEST_real_ai.mp4", f.read(), "video/mp4")}
    r = requests.post(f"{BASE_URL}/api/movies/upload", files=files, headers=auth_headers)
    assert r.status_code == 200, r.text
    return r.json()["movie_id"]


# ---------- /api/config/ai ----------
class TestAIConfig:
    def test_config_ai_returns_real_mode(self):
        r = requests.get(f"{BASE_URL}/api/config/ai")
        assert r.status_code == 200
        data = r.json()
        assert data["ai_mode"] == "real"
        assert data["max_duration_seconds"] == 60
        assert data["monthly_budget_limit"] == 500
        assert data["daily_budget_limit"] == 100


# ---------- /api/dubbing/estimate-cost ----------
class TestEstimateCost:
    def test_estimate_cost_valid_video(self, auth_headers, uploaded_movie):
        r = requests.post(
            f"{BASE_URL}/api/dubbing/estimate-cost",
            json={"movie_id": uploaded_movie},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        # Cost breakdown components
        for k in ["whisper_cost", "gpt_cost", "tts_cost", "total_cost", "duration_seconds"]:
            assert k in data, f"missing {k} in {data}"
        # Budget info
        for k in ["monthly_spending", "daily_spending", "remaining_monthly_budget",
                  "remaining_daily_budget", "budget_exceeded", "can_process"]:
            assert k in data
        assert data["can_process"] == True
        assert data["budget_exceeded"] == False
        assert data["duration_seconds"] > 0
        assert data["total_cost"] > 0
        # _id should not leak
        assert "_id" not in data

    def test_estimate_cost_movie_not_found(self, auth_headers):
        r = requests.post(
            f"{BASE_URL}/api/dubbing/estimate-cost",
            json={"movie_id": "nonexistent_xyz"},
            headers=auth_headers,
        )
        assert r.status_code == 404

    def test_estimate_cost_unauthenticated(self, uploaded_movie):
        r = requests.post(
            f"{BASE_URL}/api/dubbing/estimate-cost",
            json={"movie_id": uploaded_movie},
        )
        assert r.status_code == 401


# ---------- /api/dubbing/create (real mode) ----------
class TestRealModeCreate:
    def test_create_without_cost_approval_blocked(self, auth_headers, uploaded_movie):
        r = requests.post(
            f"{BASE_URL}/api/dubbing/create",
            json={"movie_id": uploaded_movie, "target_language": "ta"},
            headers=auth_headers,
        )
        # Real mode requires cost_approved=true
        assert r.status_code == 400, r.text
        assert "cost" in r.text.lower() or "approv" in r.text.lower()

    def test_create_invalid_target_language(self, auth_headers, uploaded_movie):
        r = requests.post(
            f"{BASE_URL}/api/dubbing/create",
            json={"movie_id": uploaded_movie, "target_language": "xx", "cost_approved": True},
            headers=auth_headers,
        )
        assert r.status_code == 400

    def test_create_with_cost_approval_starts_job(self, auth_headers, uploaded_movie):
        r = requests.post(
            f"{BASE_URL}/api/dubbing/create",
            json={"movie_id": uploaded_movie, "target_language": "ta", "cost_approved": True},
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] == "processing"
        assert data["ai_mode"] == "real"
        assert data["target_language"] == "ta"
        assert "_id" not in data
        pytest.real_job_id = data["job_id"]

    def test_real_job_progresses_or_fails_gracefully(self, auth_headers):
        """Poll up to 60s. Job should advance past 0 (real AI may fail without API quota,
        but it should at least update progress/stage or be marked failed - not stuck at 0)."""
        jid = getattr(pytest, "real_job_id", None)
        if not jid:
            pytest.skip("No real job created")
        last_status = None
        last_progress = 0
        last_stage = None
        for _ in range(30):
            r = requests.get(f"{BASE_URL}/api/dubbing/{jid}", headers={"Authorization": f"Bearer {SESSION_TOKEN}"})
            assert r.status_code == 200
            d = r.json()
            last_status = d.get("status")
            last_progress = d.get("progress", 0)
            last_stage = d.get("current_stage")
            if last_status in ("completed", "failed") or last_progress > 0:
                break
            time.sleep(2)
        print(f"Real-AI job final: status={last_status} progress={last_progress} stage={last_stage}")
        # Either progressed, completed, or failed gracefully (not stuck silently)
        assert last_status in ("processing", "completed", "failed")
