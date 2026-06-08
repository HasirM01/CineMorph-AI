from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Request, Response, Cookie
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import aiofiles
import asyncio
import httpx
import subprocess
import json
from emergentintegrations.llm.openai import OpenAISpeechToText, OpenAITextToSpeech
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

STORAGE_DIR = ROOT_DIR / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
PROCESSED_DIR = STORAGE_DIR / "processed"
TEMP_DIR = STORAGE_DIR / "temp"

for dir_path in [UPLOADS_DIR, PROCESSED_DIR, TEMP_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

MAX_UPLOAD_SIZE = 500 * 1024 * 1024
AI_MODE = os.environ.get('AI_MODE', 'mock')  # 'mock' or 'real'
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# AI Cost Configuration (approximate rates)
WHISPER_COST_PER_MINUTE = 0.006  # $0.006 per minute
GPT4O_INPUT_COST_PER_1M = 2.50   # $2.50 per 1M input tokens
GPT4O_OUTPUT_COST_PER_1M = 10.00 # $10 per 1M output tokens
TTS_COST_PER_1M_CHARS = 15.00    # $15 per 1M characters (tts-1)

# Budget limits
MONTHLY_BUDGET_LIMIT = 500  # ₹500 or equivalent in credits
DAILY_BUDGET_LIMIT = 100    # ₹100 per day

# Duration limits for POC
MAX_VIDEO_DURATION_SECONDS = 60  # 1 minute max

# ==================== Helper Functions ====================

def parse_range_header(range_header: str, file_size: int):
    """Parse HTTP Range header and return start, end positions"""
    try:
        range_str = range_header.replace("bytes=", "")
        start, end = range_str.split("-")
        start = int(start) if start else 0
        end = int(end) if end else file_size - 1
        
        if start >= file_size or end >= file_size:
            return None, None
        
        return start, end
    except:
        return None, None

async def range_file_reader(file_path: Path, start: int, end: int, chunk_size: int = 8192):
    """Generator to read file in chunks for Range requests"""
    async with aiofiles.open(file_path, 'rb') as f:
        await f.seek(start)
        remaining = end - start + 1
        
        while remaining > 0:
            chunk = await f.read(min(chunk_size, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk

def get_video_duration(video_path: Path) -> float:
    """Get video duration in seconds using FFprobe"""
    try:
        result = subprocess.run(
            [
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'json',
                str(video_path)
            ],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        duration = float(data['format']['duration'])
        if duration <= 0:
            raise ValueError(f"Invalid video duration: {duration}")
        return duration
    except Exception as e:
        logger.error(f"Failed to get video duration: {e}")
        raise HTTPException(status_code=400, detail=f"Could not determine video duration: {str(e)}")

def estimate_translation_tokens(text: str, target_language: str) -> dict:
    """Estimate GPT-4o tokens for translation"""
    # Rough estimate: ~1.3 tokens per word for English
    # System prompt adds ~100 tokens
    # Target language adds ~50 tokens
    words = len(text.split())
    input_tokens = int(words * 1.3) + 150
    # Output is usually similar length or slightly longer
    output_tokens = int(words * 1.5)
    
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost": (input_tokens / 1_000_000) * GPT4O_INPUT_COST_PER_1M,
        "output_cost": (output_tokens / 1_000_000) * GPT4O_OUTPUT_COST_PER_1M
    }

async def calculate_processing_cost(video_path: Path, estimated_duration: float = None) -> dict:
    """Calculate estimated cost for processing a video"""
    if estimated_duration is None:
        estimated_duration = get_video_duration(video_path)
    
    duration_minutes = estimated_duration / 60.0
    
    # Whisper cost
    whisper_cost = duration_minutes * WHISPER_COST_PER_MINUTE
    
    # Estimate transcription length (rough: 150 words per minute)
    estimated_words = int(duration_minutes * 150)
    estimated_text = " ".join(["word"] * estimated_words)
    
    # GPT-4o translation cost
    translation_estimate = estimate_translation_tokens(estimated_text, "ta")
    gpt_cost = translation_estimate["input_cost"] + translation_estimate["output_cost"]
    
    # TTS cost (character count approximately 5 chars per word)
    estimated_chars = estimated_words * 5
    tts_cost = (estimated_chars / 1_000_000) * TTS_COST_PER_1M_CHARS
    
    total_cost = whisper_cost + gpt_cost + tts_cost
    
    # Estimate processing time: ~1.5x video duration + 30s overhead
    estimated_time_minutes = max(1, int((estimated_duration * 1.5 + 30) / 60))
    
    return {
        "duration_seconds": estimated_duration,
        "duration_minutes": duration_minutes,
        "whisper_cost": round(whisper_cost, 4),
        "gpt_cost": round(gpt_cost, 4),
        "tts_cost": round(tts_cost, 4),
        "total_cost": round(total_cost, 4),
        "estimated_processing_time": estimated_time_minutes
    }

async def get_user_spending(user_id: str, period: str = "monthly") -> float:
    """Get user's total spending for a period"""
    now = datetime.now(timezone.utc)
    
    if period == "daily":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    else:  # monthly
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    jobs = await db.dubbing_jobs.find({
        "user_id": user_id,
        "status": "completed",
        "completed_at": {"$gte": start_date.isoformat()}
    }, {"_id": 0}).to_list(1000)
    
    total_cost = sum(job.get("actual_cost", 0) for job in jobs)
    return total_cost

def get_language_code_iso(lang_code: str) -> str:
    """Map our language codes to ISO 639-2 codes for FFmpeg metadata"""
    iso_map = {
        "en": "eng",
        "ta": "tam",
        "te": "tel",
        "ml": "mal",
        "kn": "kan",
        "hi": "hin",
        "es": "spa",
        "fr": "fra",
        "de": "deu",
        "ja": "jpn",
        "ko": "kor",
        "zh": "chi",
        "ar": "ara",
        "pt": "por",
        "ru": "rus"
    }
    return iso_map.get(lang_code, "und")

def get_language_name(lang_code: str) -> str:
    """Get full language name"""
    for lang in LANGUAGES:
        if lang["code"] == lang_code:
            return lang["name"]
    return "Unknown"


async def recover_orphaned_jobs():
    """
    Recover orphaned processing jobs on startup
    Mark jobs as failed if they were processing when server restarted
    """
    logger.info("Starting orphaned job recovery...")
    
    cutoff_time = datetime.now(timezone.utc)
    
    orphaned_jobs = await db.dubbing_jobs.find({
        "status": "processing"
    }, {"_id": 0}).to_list(1000)
    
    recovered_count = 0
    for job in orphaned_jobs:
        last_heartbeat = job.get("last_heartbeat")
        
        if last_heartbeat:
            if isinstance(last_heartbeat, str):
                last_heartbeat = datetime.fromisoformat(last_heartbeat)
            if last_heartbeat.tzinfo is None:
                last_heartbeat = last_heartbeat.replace(tzinfo=timezone.utc)
            
            time_diff = (cutoff_time - last_heartbeat).total_seconds()
            
            if time_diff > 60:
                await db.dubbing_jobs.update_one(
                    {"job_id": job["job_id"]},
                    {"$set": {
                        "status": "failed",
                        "current_stage": "Failed: Server restart during processing",
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                recovered_count += 1
                logger.warning(f"Marked orphaned job as failed: {job['job_id']}")
        else:
            await db.dubbing_jobs.update_one(
                {"job_id": job["job_id"]},
                {"$set": {
                    "status": "failed",
                    "current_stage": "Failed: Server restart during processing",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            recovered_count += 1
            logger.warning(f"Marked orphaned job as failed: {job['job_id']}")
    
    logger.info(f"Orphaned job recovery complete. Recovered {recovered_count} jobs.")
    return recovered_count

# ==================== Models ====================

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime

class UserSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime

class Movie(BaseModel):
    model_config = ConfigDict(extra="ignore")
    movie_id: str
    user_id: str
    title: str
    original_filename: str
    file_path: str
    file_size: int
    format: str
    detected_language: Optional[str] = None
    duration: Optional[int] = None
    uploaded_at: datetime

class DubbingJob(BaseModel):
    model_config = ConfigDict(extra="ignore")
    job_id: str
    user_id: str
    movie_id: str
    source_language: str
    target_language: str
    status: str
    progress: int
    current_stage: str
    output_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

class Language(BaseModel):
    code: str
    name: str
    native_name: str

class AnalyticsResponse(BaseModel):
    total_uploads: int
    total_dubbing_jobs: int
    completed_jobs: int
    in_progress_jobs: int
    failed_jobs: int
    languages_used: dict

# ==================== Auth Helper ====================

async def get_current_user(request: Request, session_token: Optional[str] = Cookie(None)) -> dict:
    """
    REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    """
    token = session_token
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session_doc = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session_doc:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    expires_at = session_doc["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    
    user_doc = await db.users.find_one({"user_id": session_doc["user_id"]}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user_doc

# ==================== Auth Routes ====================

@api_router.post("/auth/session")
async def exchange_session(request: Request, response: Response):
    """
    REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    """
    data = await request.json()
    session_id = data.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
    
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Invalid session_id")
    
    oauth_data = resp.json()
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    existing_user = await db.users.find_one({"email": oauth_data["email"]}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "name": oauth_data["name"],
                "picture": oauth_data.get("picture")
            }}
        )
    else:
        user_doc = {
            "user_id": user_id,
            "email": oauth_data["email"],
            "name": oauth_data["name"],
            "picture": oauth_data.get("picture"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)
    
    session_token = oauth_data["session_token"]
    
    await db.user_sessions.update_one(
        {"session_token": session_token},
        {"$set": {
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=7 * 24 * 60 * 60,
        path="/"
    )
    
    user_data = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return user_data

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

@api_router.post("/auth/logout")
async def logout(response: Response, session_token: Optional[str] = Cookie(None)):
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/", samesite="none", secure=True)
    return {"message": "Logged out successfully"}

# ==================== Languages Route ====================

LANGUAGES = [
    {"code": "ta", "name": "Tamil", "native_name": "தமிழ்"},
    {"code": "te", "name": "Telugu", "native_name": "తెలుగు"},
    {"code": "ml", "name": "Malayalam", "native_name": "മലയാളം"},
    {"code": "kn", "name": "Kannada", "native_name": "ಕನ್ನಡ"},
    {"code": "hi", "name": "Hindi", "native_name": "हिन्दी"},
    {"code": "en", "name": "English", "native_name": "English"},
    {"code": "es", "name": "Spanish", "native_name": "Español"},
    {"code": "fr", "name": "French", "native_name": "Français"},
    {"code": "de", "name": "German", "native_name": "Deutsch"},
    {"code": "ja", "name": "Japanese", "native_name": "日本語"},
    {"code": "ko", "name": "Korean", "native_name": "한국어"},
    {"code": "zh", "name": "Chinese", "native_name": "中文"},
    {"code": "ar", "name": "Arabic", "native_name": "العربية"},
    {"code": "pt", "name": "Portuguese", "native_name": "Português"},
    {"code": "ru", "name": "Russian", "native_name": "Русский"},
]

VALID_LANGUAGE_CODES = {lang["code"] for lang in LANGUAGES}

@api_router.get("/languages")
async def get_languages():
    return LANGUAGES


@api_router.get("/config/ai")
async def get_ai_config():
    """Get AI processing configuration"""
    return {
        "ai_mode": AI_MODE,
        "max_duration_seconds": MAX_VIDEO_DURATION_SECONDS,
        "monthly_budget_limit": MONTHLY_BUDGET_LIMIT,
        "daily_budget_limit": DAILY_BUDGET_LIMIT
    }


# ==================== Movie Upload Routes ====================

@api_router.post("/movies/upload")
async def upload_movie(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    allowed_formats = ["mp4", "mkv", "avi"]
    file_ext = file.filename.split(".")[-1].lower()
    
    if file_ext not in allowed_formats:
        raise HTTPException(status_code=400, detail=f"Format not supported. Allowed: {', '.join(allowed_formats)}")
    
    movie_id = f"movie_{uuid.uuid4().hex[:12]}"
    file_path = UPLOADS_DIR / f"{movie_id}.{file_ext}"
    
    file_size = 0
    async with aiofiles.open(file_path, 'wb') as f:
        while chunk := await file.read(1024 * 1024):
            file_size += len(chunk)
            if file_size > MAX_UPLOAD_SIZE:
                await f.close()
                file_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail=f"File too large. Max size: {MAX_UPLOAD_SIZE / (1024*1024):.0f} MB")
            await f.write(chunk)
    
    logger.info(f"Movie uploaded: {movie_id}, size: {file_size} bytes, user: {current_user['user_id']}")
    
    detected_language = "en"
    
    movie_doc = {
        "movie_id": movie_id,
        "user_id": current_user["user_id"],
        "title": file.filename,
        "original_filename": file.filename,
        "file_path": str(file_path),
        "file_size": file_size,
        "format": file_ext,
        "detected_language": detected_language,
        "duration": 0,
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    await db.movies.insert_one(movie_doc)
    
    movie_result = await db.movies.find_one({"movie_id": movie_id}, {"_id": 0})
    return movie_result

@api_router.get("/movies")
async def get_movies(current_user: dict = Depends(get_current_user)):
    movies = await db.movies.find({"user_id": current_user["user_id"]}, {"_id": 0}).sort("uploaded_at", -1).to_list(100)
    return movies

@api_router.get("/movies/{movie_id}")
async def get_movie(movie_id: str, current_user: dict = Depends(get_current_user)):
    movie = await db.movies.find_one({"movie_id": movie_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie

@api_router.delete("/movies/{movie_id}")
async def delete_movie(movie_id: str, current_user: dict = Depends(get_current_user)):
    movie = await db.movies.find_one({"movie_id": movie_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    if Path(movie["file_path"]).exists():
        Path(movie["file_path"]).unlink()
        logger.info(f"Deleted movie file: {movie['file_path']}")
    
    related_jobs = await db.dubbing_jobs.find({"movie_id": movie_id}, {"_id": 0}).to_list(100)
    for job in related_jobs:
        if job.get("output_path") and Path(job["output_path"]).exists():
            Path(job["output_path"]).unlink()
            logger.info(f"Deleted dubbed output: {job['output_path']}")
    
    await db.movies.delete_one({"movie_id": movie_id})
    await db.dubbing_jobs.delete_many({"movie_id": movie_id})
    
    logger.info(f"Deleted movie and related jobs: {movie_id}")
    return {"message": "Movie and related dubbing jobs deleted successfully"}

@api_router.get("/movies/{movie_id}/stream")
async def stream_movie(
    movie_id: str, 
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    movie = await db.movies.find_one({"movie_id": movie_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    file_path = Path(movie["file_path"])
    if not file_path.exists():
        logger.error(f"Movie file not found: {file_path}")
        raise HTTPException(status_code=404, detail="Movie file not found on server")
    
    file_size = file_path.stat().st_size
    range_header = request.headers.get("range")
    
    if range_header:
        start, end = parse_range_header(range_header, file_size)
        
        if start is None or end is None:
            raise HTTPException(status_code=416, detail="Range not satisfiable")
        
        content_length = end - start + 1
        
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Type": "video/mp4",
        }
        
        logger.info(f"Streaming movie {movie_id} with range: {start}-{end}/{file_size}")
        
        return StreamingResponse(
            range_file_reader(file_path, start, end),
            status_code=206,
            headers=headers,
            media_type="video/mp4"
        )
    else:
        headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Type": "video/mp4",
        }
        
        logger.info(f"Streaming full movie {movie_id}")
        
        return StreamingResponse(
            range_file_reader(file_path, 0, file_size - 1),
            headers=headers,
            media_type="video/mp4"
        )

# ==================== Dubbing Job Routes ====================

async def mock_ai_processing(job_id: str, movie_id: str, source_lang: str, target_lang: str, user_id: str):
    """
    Mock AI dubbing pipeline with realistic processing stages
    """
    stages = [
        {"stage": "Extracting Audio", "progress": 15, "delay": 2},
        {"stage": "Detecting Language", "progress": 30, "delay": 3},
        {"stage": "Transcribing Speech", "progress": 50, "delay": 4},
        {"stage": "Translating Dialogues", "progress": 70, "delay": 3},
        {"stage": "Generating AI Voices", "progress": 85, "delay": 4},
        {"stage": "Synchronizing Audio", "progress": 95, "delay": 2},
        {"stage": "Finalizing Output", "progress": 100, "delay": 2},
    ]
    
    try:
        for stage_info in stages:
            job = await db.dubbing_jobs.find_one({"job_id": job_id}, {"_id": 0})
            if not job or job["status"] == "cancelled":
                logger.info(f"Job {job_id} was cancelled")
                return
            
            await asyncio.sleep(stage_info["delay"])
            await db.dubbing_jobs.update_one(
                {"job_id": job_id},
                {"$set": {
                    "current_stage": stage_info["stage"],
                    "progress": stage_info["progress"],
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "last_heartbeat": datetime.now(timezone.utc).isoformat()
                }}
            )
            logger.info(f"Job {job_id}: {stage_info['stage']} - {stage_info['progress']}%")
        
        movie = await db.movies.find_one({"movie_id": movie_id}, {"_id": 0})
        output_filename = f"{job_id}_dubbed.mp4"
        output_path = PROCESSED_DIR / output_filename
        
        if movie and Path(movie["file_path"]).exists():
            import shutil
            shutil.copy(movie["file_path"], output_path)
            logger.info(f"Created dubbed output: {output_path}")
        
        await db.dubbing_jobs.update_one(
            {"job_id": job_id},
            {"$set": {
                "status": "completed",
                "progress": 100,
                "current_stage": "Completed",
                "output_path": str(output_path),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "last_heartbeat": datetime.now(timezone.utc).isoformat()
            }}
        )
        logger.info(f"Job {job_id} completed successfully")
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        await db.dubbing_jobs.update_one(
            {"job_id": job_id},
            {"$set": {
                "status": "failed",
                "current_stage": f"Failed: {str(e)}",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )


async def real_ai_processing(job_id: str, movie_id: str, source_lang: str, target_lang: str, user_id: str):
    """
    Real AI dubbing pipeline using Whisper + GPT-4o + OpenAI TTS
    Creates multi-audio track output with original and dubbed audio
    """
    temp_audio_path = None
    temp_dubbed_audio_path = None
    actual_costs = {"whisper": 0, "gpt": 0, "tts": 0, "total": 0}
    
    try:
        # Stage 1: Extract Audio
        await db.dubbing_jobs.update_one(
            {"job_id": job_id},
            {"$set": {
                "current_stage": "Extracting Audio",
                "progress": 10,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "last_heartbeat": datetime.now(timezone.utc).isoformat()
            }}
        )
        logger.info(f"Job {job_id}: Extracting audio...")
        
        movie = await db.movies.find_one({"movie_id": movie_id}, {"_id": 0})
        if not movie:
            raise Exception("Movie not found")
        
        video_path = Path(movie["file_path"])
        if not video_path.exists():
            raise Exception("Video file not found")
        
        # Extract audio to temp file
        temp_audio_path = TEMP_DIR / f"{job_id}_audio.mp3"
        subprocess.run(
            [
                'ffmpeg', '-i', str(video_path),
                '-vn', '-acodec', 'mp3',
                '-y', str(temp_audio_path)
            ],
            check=True,
            capture_output=True
        )
        logger.info(f"Audio extracted to {temp_audio_path}")
        
        # Stage 2: Transcribe with Whisper
        await db.dubbing_jobs.update_one(
            {"job_id": job_id},
            {"$set": {
                "current_stage": "Transcribing Speech (Whisper)",
                "progress": 30,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "last_heartbeat": datetime.now(timezone.utc).isoformat()
            }}
        )
        logger.info(f"Job {job_id}: Transcribing with Whisper...")
        
        stt = OpenAISpeechToText(api_key=EMERGENT_LLM_KEY)
        with open(temp_audio_path, "rb") as audio_file:
            whisper_response = await stt.transcribe(
                file=audio_file,
                model="whisper-1",
                response_format="verbose_json"
            )
        
        transcribed_text = whisper_response.text
        detected_language = whisper_response.language if hasattr(whisper_response, 'language') else source_lang
        
        # Calculate Whisper cost
        duration = whisper_response.duration if hasattr(whisper_response, 'duration') else get_video_duration(video_path)
        actual_costs["whisper"] = (duration / 60.0) * WHISPER_COST_PER_MINUTE
        
        logger.info(f"Transcription complete. Detected language: {detected_language}")
        logger.info(f"Transcribed text length: {len(transcribed_text)} characters")
        
        # Stage 3: Translate with GPT-4o
        await db.dubbing_jobs.update_one(
            {"job_id": job_id},
            {"$set": {
                "current_stage": "Translating Dialogues (GPT-4o)",
                "progress": 50,
                "detected_language": detected_language,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "last_heartbeat": datetime.now(timezone.utc).isoformat()
            }}
        )
        logger.info(f"Job {job_id}: Translating with GPT-4o...")
        
        # Conversational translation prompts for South Indian languages
        target_lang_name = get_language_name(target_lang)
        
        translation_prompts = {
            "ta": "You are a professional Tamil cinema dialogue translator. Translate the following text to modern spoken conversational Tamil as used in contemporary Tamil cinema. Use natural, colloquial Tamil that sounds authentic to Tamil movie audiences. Avoid formal textbook Tamil. Preserve the emotional tone, context, and meaning of the original dialogue. Only return the translated text, nothing else.",
            "te": "You are a professional Telugu cinema dialogue translator. Translate the following text to natural spoken conversational Telugu as used in Telugu cinema. Use authentic colloquial Telugu that resonates with Telugu movie audiences. Preserve emotions, context, and meaning. Only return the translated text, nothing else.",
            "ml": "You are a professional Malayalam cinema dialogue translator. Translate the following text to natural spoken conversational Malayalam as used in Malayalam cinema. Use authentic colloquial Malayalam. Preserve emotions, context, and meaning. Only return the translated text, nothing else.",
            "kn": "You are a professional Kannada cinema dialogue translator. Translate the following text to natural spoken conversational Kannada as used in Kannada cinema. Use authentic colloquial Kannada. Preserve emotions, context, and meaning. Only return the translated text, nothing else."
        }
        
        system_prompt = translation_prompts.get(
            target_lang,
            f"You are a professional translator. Translate the following text to natural spoken conversational {target_lang_name}. Preserve emotions, context, and meaning. Only return the translated text, nothing else."
        )
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"translation_{job_id}",
            system_message=system_prompt
        ).with_model("openai", "gpt-4o")
        
        user_message = UserMessage(text=transcribed_text)
        response_text = await chat.send_message(user_message)
        translated_text = response_text
        
        # Estimate GPT cost (rough approximation)
        token_estimate = estimate_translation_tokens(transcribed_text, target_lang)
        actual_costs["gpt"] = token_estimate["input_cost"] + token_estimate["output_cost"]
        
        logger.info(f"Translation complete. Translated text length: {len(translated_text)} characters")
        
        # Stage 4: Generate Voice with OpenAI TTS
        await db.dubbing_jobs.update_one(
            {"job_id": job_id},
            {"$set": {
                "current_stage": "Generating AI Voice (OpenAI TTS)",
                "progress": 70,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "last_heartbeat": datetime.now(timezone.utc).isoformat()
            }}
        )
        logger.info(f"Job {job_id}: Generating voice with OpenAI TTS...")
        
        tts = OpenAITextToSpeech(api_key=EMERGENT_LLM_KEY)
        temp_dubbed_audio_path = TEMP_DIR / f"{job_id}_dubbed_audio.mp3"
        
        audio_bytes = await tts.generate_speech(
            text=translated_text,
            model="tts-1",
            voice="alloy",
            response_format="mp3"
        )
        
        with open(temp_dubbed_audio_path, "wb") as f:
            f.write(audio_bytes)
        
        # Calculate TTS cost
        actual_costs["tts"] = (len(translated_text) / 1_000_000) * TTS_COST_PER_1M_CHARS
        actual_costs["total"] = sum(actual_costs.values())
        
        logger.info(f"Voice generation complete. Audio saved to {temp_dubbed_audio_path}")
        
        # Stage 5: Create Multi-Audio Track Video
        await db.dubbing_jobs.update_one(
            {"job_id": job_id},
            {"$set": {
                "current_stage": "Creating Multi-Audio Track Output",
                "progress": 90,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "last_heartbeat": datetime.now(timezone.utc).isoformat()
            }}
        )
        logger.info(f"Job {job_id}: Creating multi-audio track video...")
        
        output_filename = f"{job_id}_dubbed.mp4"
        output_path = PROCESSED_DIR / output_filename
        
        source_lang_iso = get_language_code_iso(detected_language)
        target_lang_iso = get_language_code_iso(target_lang)
        source_lang_name = get_language_name(detected_language)
        target_lang_name = get_language_name(target_lang)
        
        # FFmpeg command for multi-audio track muxing
        subprocess.run(
            [
                'ffmpeg',
                '-i', str(video_path),              # Input: original video
                '-i', str(temp_dubbed_audio_path),  # Input: dubbed audio
                '-map', '0:v',                      # Map video from first input
                '-map', '0:a',                      # Map original audio from first input
                '-map', '1:a',                      # Map dubbed audio from second input
                '-metadata:s:a:0', f'language={source_lang_iso}',
                '-metadata:s:a:0', f'title={source_lang_name} (Original)',
                '-metadata:s:a:1', f'language={target_lang_iso}',
                '-metadata:s:a:1', f'title={target_lang_name} (Dubbed)',
                '-c:v', 'copy',                     # Copy video codec (no re-encoding)
                '-c:a', 'aac',                      # Encode audio as AAC
                '-b:a', '192k',                     # Audio bitrate
                '-y',                               # Overwrite output
                str(output_path)
            ],
            check=True,
            capture_output=True
        )
        
        logger.info(f"Multi-audio track video created: {output_path}")
        
        # Stage 6: Complete
        await db.dubbing_jobs.update_one(
            {"job_id": job_id},
            {"$set": {
                "status": "completed",
                "progress": 100,
                "current_stage": "Completed",
                "output_path": str(output_path),
                "detected_language": detected_language,
                "actual_cost": round(actual_costs["total"], 4),
                "cost_breakdown": {
                    "whisper": round(actual_costs["whisper"], 4),
                    "gpt": round(actual_costs["gpt"], 4),
                    "tts": round(actual_costs["tts"], 4)
                },
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "last_heartbeat": datetime.now(timezone.utc).isoformat()
            }}
        )
        logger.info(f"Job {job_id} completed successfully. Total cost: ${actual_costs['total']:.4f}")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)
        await db.dubbing_jobs.update_one(
            {"job_id": job_id},
            {"$set": {
                "status": "failed",
                "current_stage": f"Failed: {str(e)}",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    finally:
        # Cleanup temp files
        if temp_audio_path and Path(temp_audio_path).exists():
            Path(temp_audio_path).unlink()
            logger.info(f"Cleaned up temp audio: {temp_audio_path}")
        if temp_dubbed_audio_path and Path(temp_dubbed_audio_path).exists():
            Path(temp_dubbed_audio_path).unlink()
            logger.info(f"Cleaned up temp dubbed audio: {temp_dubbed_audio_path}")



@api_router.post("/dubbing/estimate-cost")
async def estimate_dubbing_cost(request: Request, current_user: dict = Depends(get_current_user)):
    """Estimate processing cost for a video"""
    data = await request.json()
    movie_id = data.get("movie_id")
    
    movie = await db.movies.find_one({"movie_id": movie_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    video_path = Path(movie["file_path"])
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    
    # Check video duration
    duration = get_video_duration(video_path)
    if duration > MAX_VIDEO_DURATION_SECONDS:
        raise HTTPException(
            status_code=400,
            detail=f"Video duration ({int(duration)}s) exceeds maximum allowed ({MAX_VIDEO_DURATION_SECONDS}s). Please use clips of 30 seconds or 1 minute for this POC."
        )
    
    cost_estimate = await calculate_processing_cost(video_path, duration)
    
    # Check budget limits
    monthly_spending = await get_user_spending(current_user["user_id"], "monthly")
    daily_spending = await get_user_spending(current_user["user_id"], "daily")
    
    remaining_monthly = MONTHLY_BUDGET_LIMIT - monthly_spending
    remaining_daily = DAILY_BUDGET_LIMIT - daily_spending
    
    budget_exceeded = False
    budget_warning = None
    
    if cost_estimate["total_cost"] > remaining_monthly:
        budget_exceeded = True
        budget_warning = f"Processing would exceed monthly budget limit (₹{MONTHLY_BUDGET_LIMIT}). Remaining: ₹{remaining_monthly:.2f}"
    elif cost_estimate["total_cost"] > remaining_daily:
        budget_exceeded = True
        budget_warning = f"Processing would exceed daily budget limit (₹{DAILY_BUDGET_LIMIT}). Remaining: ₹{remaining_daily:.2f}"
    
    return {
        **cost_estimate,
        "monthly_spending": round(monthly_spending, 2),
        "daily_spending": round(daily_spending, 2),
        "remaining_monthly_budget": round(remaining_monthly, 2),
        "remaining_daily_budget": round(remaining_daily, 2),
        "budget_exceeded": budget_exceeded,
        "budget_warning": budget_warning,
        "can_process": not budget_exceeded
    }


@api_router.post("/dubbing/create")
async def create_dubbing_job(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    movie_id = data.get("movie_id")
    target_language = data.get("target_language")
    cost_approved = data.get("cost_approved", False)
    
    if target_language not in VALID_LANGUAGE_CODES:
        raise HTTPException(status_code=400, detail=f"Invalid target language. Must be one of: {', '.join(VALID_LANGUAGE_CODES)}")
    
    movie = await db.movies.find_one({"movie_id": movie_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # For real AI mode, check cost approval and budget
    if AI_MODE == "real":
        if not cost_approved:
            raise HTTPException(status_code=400, detail="Cost approval required. Please estimate cost first and approve before processing.")
        
        # Verify video duration
        video_path = Path(movie["file_path"])
        duration = get_video_duration(video_path)
        if duration > MAX_VIDEO_DURATION_SECONDS:
            raise HTTPException(
                status_code=400,
                detail=f"Video duration ({int(duration)}s) exceeds maximum allowed ({MAX_VIDEO_DURATION_SECONDS}s)."
            )
        
        # Check budget
        cost_estimate = await calculate_processing_cost(video_path, duration)
        monthly_spending = await get_user_spending(current_user["user_id"], "monthly")
        daily_spending = await get_user_spending(current_user["user_id"], "daily")
        
        if cost_estimate["total_cost"] + monthly_spending > MONTHLY_BUDGET_LIMIT:
            raise HTTPException(status_code=403, detail="Monthly budget limit exceeded")
        
        if cost_estimate["total_cost"] + daily_spending > DAILY_BUDGET_LIMIT:
            raise HTTPException(status_code=403, detail="Daily budget limit exceeded")
    
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    job_doc = {
        "job_id": job_id,
        "user_id": current_user["user_id"],
        "movie_id": movie_id,
        "source_language": movie.get("detected_language", "en"),
        "target_language": target_language,
        "status": "processing",
        "progress": 0,
        "current_stage": "Starting...",
        "output_path": None,
        "ai_mode": AI_MODE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "last_heartbeat": datetime.now(timezone.utc).isoformat()
    }
    await db.dubbing_jobs.insert_one(job_doc)
    
    logger.info(f"Created dubbing job: {job_id} for movie: {movie_id} (AI_MODE: {AI_MODE})")
    
    # Choose processing function based on AI_MODE
    if AI_MODE == "real":
        asyncio.create_task(real_ai_processing(
            job_id, movie_id, job_doc["source_language"], target_language, current_user["user_id"]
        ))
    else:
        asyncio.create_task(mock_ai_processing(
            job_id, movie_id, job_doc["source_language"], target_language, current_user["user_id"]
        ))
    
    job_result = await db.dubbing_jobs.find_one({"job_id": job_id}, {"_id": 0})
    return job_result

@api_router.get("/dubbing/jobs")
async def get_dubbing_jobs(current_user: dict = Depends(get_current_user)):
    jobs = await db.dubbing_jobs.find({"user_id": current_user["user_id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    for job in jobs:
        movie = await db.movies.find_one({"movie_id": job["movie_id"]}, {"_id": 0})
        if movie:
            job["movie_title"] = movie["title"]
    
    return jobs

@api_router.get("/dubbing/{job_id}")
async def get_dubbing_job(job_id: str, current_user: dict = Depends(get_current_user)):
    job = await db.dubbing_jobs.find_one({"job_id": job_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    movie = await db.movies.find_one({"movie_id": job["movie_id"]}, {"_id": 0})
    if movie:
        job["movie_title"] = movie["title"]
    
    return job

@api_router.delete("/dubbing/{job_id}")
async def delete_dubbing_job(job_id: str, current_user: dict = Depends(get_current_user)):
    job = await db.dubbing_jobs.find_one({"job_id": job_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.get("output_path") and Path(job["output_path"]).exists():
        Path(job["output_path"]).unlink()
        logger.info(f"Deleted dubbed output: {job['output_path']}")
    
    await db.dubbing_jobs.delete_one({"job_id": job_id})
    logger.info(f"Deleted dubbing job: {job_id}")
    
    return {"message": "Dubbing job deleted successfully"}

@api_router.get("/dubbing/{job_id}/download")
async def download_dubbed_movie(
    job_id: str, 
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    logger.info(f"Download request for job: {job_id} by user: {current_user['user_id']}")
    
    job = await db.dubbing_jobs.find_one({"job_id": job_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not job:
        logger.error(f"Job not found: {job_id}")
        raise HTTPException(status_code=404, detail="Dubbing job not found")
    
    if job["status"] != "completed":
        logger.error(f"Job not completed: {job_id}, status: {job['status']}")
        raise HTTPException(status_code=400, detail=f"Dubbing not completed yet. Status: {job['status']}")
    
    if not job.get("output_path"):
        logger.error(f"No output path for job: {job_id}")
        raise HTTPException(status_code=404, detail="Output file path not found in database")
    
    output_path = Path(job["output_path"])
    logger.info(f"Output path: {output_path}, exists: {output_path.exists()}")
    
    if not output_path.exists():
        logger.error(f"Output file missing: {output_path}")
        raise HTTPException(status_code=404, detail="Output file not found on server. It may have been deleted.")
    
    file_size = output_path.stat().st_size
    range_header = request.headers.get("range")
    
    if range_header:
        start, end = parse_range_header(range_header, file_size)
        
        if start is None or end is None:
            raise HTTPException(status_code=416, detail="Range not satisfiable")
        
        content_length = end - start + 1
        
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Type": "video/mp4",
            "Content-Disposition": f'attachment; filename="dubbed_{job_id}.mp4"'
        }
        
        logger.info(f"Downloading job {job_id} with range: {start}-{end}/{file_size}")
        
        return StreamingResponse(
            range_file_reader(output_path, start, end),
            status_code=206,
            headers=headers,
            media_type="video/mp4"
        )
    else:
        headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Type": "video/mp4",
            "Content-Disposition": f'attachment; filename="dubbed_{job_id}.mp4"'
        }
        
        logger.info(f"Downloading full job {job_id}")
        
        return StreamingResponse(
            range_file_reader(output_path, 0, file_size - 1),
            headers=headers,
            media_type="video/mp4"
        )

@api_router.get("/dubbing/{job_id}/stream")
async def stream_dubbed_movie(
    job_id: str, 
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    logger.info(f"Stream request for job: {job_id} by user: {current_user['user_id']}")
    
    job = await db.dubbing_jobs.find_one({"job_id": job_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Dubbing job not found")
    
    if job["status"] != "completed" or not job.get("output_path"):
        raise HTTPException(status_code=400, detail="Dubbed movie not ready for streaming")
    
    output_path = Path(job["output_path"])
    if not output_path.exists():
        logger.error(f"Output file missing for streaming: {output_path}")
        raise HTTPException(status_code=404, detail="Output file not found")
    
    file_size = output_path.stat().st_size
    range_header = request.headers.get("range")
    
    if range_header:
        start, end = parse_range_header(range_header, file_size)
        
        if start is None or end is None:
            raise HTTPException(status_code=416, detail="Range not satisfiable")
        
        content_length = end - start + 1
        
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Type": "video/mp4",
        }
        
        logger.info(f"Streaming job {job_id} with range: {start}-{end}/{file_size}")
        
        return StreamingResponse(
            range_file_reader(output_path, start, end),
            status_code=206,
            headers=headers,
            media_type="video/mp4"
        )
    else:
        headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Type": "video/mp4",
        }
        
        logger.info(f"Streaming full job {job_id}")
        
        return StreamingResponse(
            range_file_reader(output_path, 0, file_size - 1),
            headers=headers,
            media_type="video/mp4"
        )

# ==================== Analytics Route ====================

@api_router.get("/analytics/user")
async def get_user_analytics(current_user: dict = Depends(get_current_user)):
    total_uploads = await db.movies.count_documents({"user_id": current_user["user_id"]})
    total_jobs = await db.dubbing_jobs.count_documents({"user_id": current_user["user_id"]})
    completed = await db.dubbing_jobs.count_documents({"user_id": current_user["user_id"], "status": "completed"})
    in_progress = await db.dubbing_jobs.count_documents({"user_id": current_user["user_id"], "status": "processing"})
    failed = await db.dubbing_jobs.count_documents({"user_id": current_user["user_id"], "status": "failed"})
    
    jobs = await db.dubbing_jobs.find({"user_id": current_user["user_id"]}, {"_id": 0}).to_list(1000)
    languages_used = {}
    for job in jobs:
        lang = job.get("target_language", "unknown")
        languages_used[lang] = languages_used.get(lang, 0) + 1
    
    return {
        "total_uploads": total_uploads,
        "total_dubbing_jobs": total_jobs,
        "completed_jobs": completed,
        "in_progress_jobs": in_progress,
        "failed_jobs": failed,
        "languages_used": languages_used
    }

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("CineMorph AI backend starting...")
    
    # Validate FFmpeg and ffprobe availability (non-blocking)
    try:
        ffmpeg_result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if ffmpeg_result.returncode != 0:
            logger.warning("FFmpeg is not working properly - Real AI processing will be limited")
        
        ffprobe_result = subprocess.run(
            ['ffprobe', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if ffprobe_result.returncode != 0:
            logger.warning("ffprobe is not working properly - Video duration detection will fail")
        
        logger.info("✓ FFmpeg and ffprobe are available and working")
        
    except FileNotFoundError as e:
        logger.error(f"WARNING: FFmpeg or ffprobe not found in PATH: {e}")
        logger.error("Real AI processing will not work. Install FFmpeg: sudo apt-get install -y ffmpeg")
        logger.warning("Backend starting anyway to allow authentication and other features...")
        # DO NOT raise - allow backend to start for auth/basic features
    except Exception as e:
        logger.error(f"Error validating FFmpeg: {e}")
        logger.warning("Backend starting anyway...")
    
    await recover_orphaned_jobs()
    logger.info("CineMorph AI backend ready!")

@app.on_event("shutdown")
async def shutdown_db_client():
    logger.info("CineMorph AI backend shutting down...")
    client.close()
    logger.info("Database connection closed")
