import asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from app.models import (
    YouTubeRequest,
    TaskResponse,
    TaskStatusResponse,
    TaskStatus,
)
from app.services.audio_processor import generate_task_id
from app.services.task_manager import (
    get_task,
    update_task,
    process_youtube_url,
    process_uploaded_file,
    read_local_vtt,
)
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Auto VTT Studio",
    description="Generate VTT subtitles from YouTube URLs or Audio files using Google Cloud Speech-to-Text V2",
    version="1.0.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Auto VTT Studio API is running"}


@app.post("/api/transcribe/youtube", response_model=TaskResponse)
async def transcribe_youtube(
    request: YouTubeRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a transcription task for a YouTube URL.
    Returns a task ID that can be used to check the status.
    """
    task_id = generate_task_id()
    
    # Initialize task status
    update_task(
        task_id,
        TaskStatus.PENDING,
        "Task created, starting download...",
        progress=0
    )
    
    # Start background task
    background_tasks.add_task(
        process_youtube_url,
        task_id,
        request.url,
        request.language_code
    )
    
    return TaskResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        message="Task created successfully",
        progress=0
    )


@app.post("/api/transcribe/upload", response_model=TaskResponse)
async def transcribe_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language_code: str = Form(default="th-TH")
):
    """
    Start a transcription task for an uploaded audio file.
    Supports WAV, MP3, FLAC, OGG, and other common audio formats.
    """
    # Validate filename
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided"
        )
    
    # Validate file type
    allowed_extensions = {'.wav', '.mp3', '.flac', '.ogg', '.m4a', '.aac', '.wma'}
    file_ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Check file size
    file_content = await file.read()
    file_size_mb = len(file_content) / (1024 * 1024)
    
    if file_size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
        )
    
    task_id = generate_task_id()
    
    # Initialize task status
    update_task(
        task_id,
        TaskStatus.PENDING,
        "Task created, processing file...",
        progress=0
    )
    
    # Start background task
    background_tasks.add_task(
        process_uploaded_file,
        task_id,
        file_content,
        file.filename,
        language_code
    )
    
    return TaskResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        message="Task created successfully",
        progress=0
    )


@app.get("/api/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get the current status of a transcription task.
    """
    task = get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskStatusResponse(
        task_id=task["task_id"],
        status=task["status"],
        message=task["message"],
        progress=task["progress"],
        vtt_url=f"/api/task/{task_id}/download" if task.get("vtt_content") else None,
        error=task.get("error")
    )


@app.get("/api/task/{task_id}/download")
async def download_vtt(task_id: str):
    """
    Download the generated VTT file for a completed task.
    Reads from local file storage first, falls back to in-memory content.
    """
    task = get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Task not completed yet")
    
    # Try reading from local file first
    vtt_content = read_local_vtt(task_id)
    
    # Fallback to in-memory content
    if not vtt_content:
        vtt_content = task.get("vtt_content")
    
    if not vtt_content:
        raise HTTPException(status_code=404, detail="VTT content not found")
    
    return Response(
        content=vtt_content,
        media_type="text/vtt",
        headers={
            "Content-Disposition": f"attachment; filename=subtitles_{task_id}.vtt"
        }
    )


@app.get("/api/languages")
async def get_supported_languages():
    """
    Get list of supported languages for transcription.
    """
    return {
        "languages": [
            {"code": "th-TH", "name": "ไทย"},
            {"code": "en-US", "name": "อังกฤษ"},
        ],
        "default": "th-TH"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
