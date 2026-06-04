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
async def stream_movie(movie_id: str, current_user: dict = Depends(get_current_user)):
    movie = await db.movies.find_one({"movie_id": movie_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    file_path = Path(movie["file_path"])
    if not file_path.exists():
        logger.error(f"Movie file not found: {file_path}")
        raise HTTPException(status_code=404, detail="Movie file not found on server")
    
    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        filename=movie["original_filename"]
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
            await asyncio.sleep(stage_info["delay"])
            await db.dubbing_jobs.update_one(
                {"job_id": job_id},
                {"$set": {
                    "current_stage": stage_info["stage"],
                    "progress": stage_info["progress"],
                    "updated_at": datetime.now(timezone.utc).isoformat()
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
                "completed_at": datetime.now(timezone.utc).isoformat()
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

@api_router.post("/dubbing/create")
async def create_dubbing_job(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    movie_id = data.get("movie_id")
    target_language = data.get("target_language")
    
    if target_language not in VALID_LANGUAGE_CODES:
        raise HTTPException(status_code=400, detail=f"Invalid target language. Must be one of: {', '.join(VALID_LANGUAGE_CODES)}")
    
    movie = await db.movies.find_one({"movie_id": movie_id, "user_id": current_user["user_id"]}, {"_id": 0})
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
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
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None
    }
    await db.dubbing_jobs.insert_one(job_doc)
    
    logger.info(f"Created dubbing job: {job_id} for movie: {movie_id}")
    
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
async def download_dubbed_movie(job_id: str, current_user: dict = Depends(get_current_user)):
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
    
    logger.info(f"Sending file: {output_path.name} for job: {job_id}")
    return FileResponse(
        path=output_path,
        filename=f"dubbed_{job_id}.mp4",
        media_type="video/mp4"
    )

@api_router.get("/dubbing/{job_id}/stream")
async def stream_dubbed_movie(job_id: str, current_user: dict = Depends(get_current_user)):
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
    
    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"dubbed_{job_id}.mp4"
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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
