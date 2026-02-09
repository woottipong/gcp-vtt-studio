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
from app.config import get_settings
from app.constants import (
    CORS_ORIGINS,
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE,
    MSG_TASK_NOT_FOUND,
    MSG_TASK_NOT_COMPLETED,
    MSG_VTT_NOT_FOUND,
    MSG_TASK_PENDING,
    MSG_TASK_PROCESSING,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)
from app.validators import validate_uploaded_file
from app.utils import create_task_response, format_vtt_filename, get_vtt_download_url
from app.services.audio_processor import generate_task_id
from app.services.task_manager import (
    get_task,
    update_task,
    process_youtube_url,
    process_uploaded_file,
    read_local_vtt,
)

settings = get_settings()

app = FastAPI(
    title="Auto VTT Studio",
    description="Generate VTT subtitles from YouTube URLs or Audio files using Google Cloud Speech-to-Text V2",
    version="1.0.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
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
        MSG_TASK_PENDING,
        progress=0
    )
    
    # Start background task
    background_tasks.add_task(
        process_youtube_url,
        task_id,
        request.url,
        request.language_code
    )
    
    return create_task_response(task_id)


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
    # Read file content
    file_content = await file.read()
    
    # Validate file (filename, format, size)
    validated_filename, _, _ = validate_uploaded_file(
        file.filename,
        file_content,
        settings.max_file_size_mb
    )
    
    task_id = generate_task_id()
    
    # Initialize task status
    update_task(
        task_id,
        TaskStatus.PENDING,
        MSG_TASK_PROCESSING,
        progress=0
    )
    
    # Start background task
    background_tasks.add_task(
        process_uploaded_file,
        task_id,
        file_content,
        validated_filename,
        language_code
    )
    
    return create_task_response(task_id)


@app.get("/api/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get the current status of a transcription task.
    """
    task = get_task(task_id)
    
    if not task:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=MSG_TASK_NOT_FOUND
        )
    
    return TaskStatusResponse(
        task_id=task["task_id"],
        status=task["status"],
        message=task["message"],
        progress=task["progress"],
        vtt_url=get_vtt_download_url(task_id) if task.get("vtt_content") else None,
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
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=MSG_TASK_NOT_FOUND
        )
    
    if task["status"] != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=MSG_TASK_NOT_COMPLETED
        )
    
    # Try reading from local file first
    vtt_content = read_local_vtt(task_id)
    
    # Fallback to in-memory content
    if not vtt_content:
        vtt_content = task.get("vtt_content")
    
    if not vtt_content:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=MSG_VTT_NOT_FOUND
        )
    
    return Response(
        content=vtt_content,
        media_type="text/vtt",
        headers={
            "Content-Disposition": f"attachment; filename={format_vtt_filename(task_id)}"
        }
    )


@app.get("/api/languages")
async def get_supported_languages():
    """
    Get list of supported languages for transcription.
    """
    return {
        "languages": SUPPORTED_LANGUAGES,
        "default": DEFAULT_LANGUAGE
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
