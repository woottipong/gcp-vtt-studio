import asyncio
import os
from pathlib import Path
from typing import Dict, Optional
from app.models import TaskStatus
from app.config import get_settings
from app.services.audio_processor import (
    download_youtube_audio,
    convert_to_mono_16khz,
    save_uploaded_file,
    cleanup_task_files,
)
from app.services.gcp_service import (
    upload_to_gcs,
    transcribe_audio,
    delete_from_gcs,
)

# In-memory task storage (use Redis or database in production)
tasks: Dict[str, dict] = {}

settings = get_settings()


def ensure_vtt_output_dir() -> Path:
    """Ensure the VTT output directory exists."""
    vtt_dir = Path(settings.vtt_output_dir)
    vtt_dir.mkdir(parents=True, exist_ok=True)
    return vtt_dir


def save_vtt_locally(task_id: str, vtt_content: str) -> str:
    """
    Save VTT content to a local file.
    Returns the absolute path to the saved VTT file.
    """
    vtt_dir = ensure_vtt_output_dir()
    vtt_path = vtt_dir / f"{task_id}.vtt"
    vtt_path.write_text(vtt_content, encoding="utf-8")
    print(f"VTT saved locally: {vtt_path}")
    return str(vtt_path.resolve())


def get_local_vtt_path(task_id: str) -> Optional[str]:
    """Get the local path to a VTT file if it exists."""
    vtt_dir = Path(settings.vtt_output_dir)
    vtt_path = vtt_dir / f"{task_id}.vtt"
    if vtt_path.exists():
        return str(vtt_path.resolve())
    return None


def read_local_vtt(task_id: str) -> Optional[str]:
    """Read VTT content from local file."""
    vtt_path = get_local_vtt_path(task_id)
    if vtt_path:
        return Path(vtt_path).read_text(encoding="utf-8")
    return None


def get_task(task_id: str) -> Optional[dict]:
    """Get task status from storage."""
    return tasks.get(task_id)


def update_task(
    task_id: str,
    status: TaskStatus,
    message: str,
    progress: int = 0,
    vtt_content: Optional[str] = None,
    error: Optional[str] = None,
) -> None:
    """Update task status in storage."""
    if task_id not in tasks:
        tasks[task_id] = {}
    
    tasks[task_id].update({
        "task_id": task_id,
        "status": status,
        "message": message,
        "progress": progress,
        "vtt_content": vtt_content,
        "error": error,
    })


async def process_youtube_url(task_id: str, url: str, language_code: str) -> None:
    """
    Async task to process a YouTube URL and generate VTT.
    """
    gcs_uri = None
    
    try:
        # Step 1: Download audio from YouTube
        update_task(
            task_id, 
            TaskStatus.DOWNLOADING, 
            "Downloading audio from YouTube...",
            progress=10
        )
        
        print(f"DEBUG: Starting task {task_id} for URL {url}")
        audio_path = await asyncio.wait_for(
            asyncio.to_thread(download_youtube_audio, url, task_id),
            timeout=settings.youtube_download_timeout
        )
        print(f"DEBUG: Downloaded audio to {audio_path}")
        
        # Step 2: Convert to mono 16kHz
        update_task(
            task_id,
            TaskStatus.CONVERTING,
            "Converting audio to mono 16kHz WAV...",
            progress=30
        )
        
        converted_path = await asyncio.to_thread(convert_to_mono_16khz, audio_path, task_id)
        
        # Log audio duration for debugging
        try:
            import subprocess as _sp
            probe = _sp.run(
                ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', converted_path],
                capture_output=True, text=True
            )
            if probe.returncode == 0:
                dur = float(probe.stdout.strip())
                print(f"DEBUG: Audio duration: {dur:.1f}s ({dur/60:.1f} min)")
        except Exception:
            pass
        
        # Step 3: Upload to GCS
        update_task(
            task_id,
            TaskStatus.UPLOADING,
            "Uploading audio to Google Cloud Storage...",
            progress=50
        )
        
        gcs_uri = await asyncio.to_thread(upload_to_gcs, converted_path, task_id)
        
        # Step 4: Transcribe using Speech-to-Text V2
        update_task(
            task_id,
            TaskStatus.TRANSCRIBING,
            "Transcribing audio (this may take a while)...",
            progress=70
        )
        
        # Get VTT content directly from STT inline results
        vtt_content = await asyncio.to_thread(
            transcribe_audio, 
            gcs_uri, 
            task_id,
            language_code
        )
        
        # Save VTT locally
        vtt_local_path = await asyncio.to_thread(save_vtt_locally, task_id, vtt_content)
        
        # Step 5: Complete
        print(f"DEBUG: Task {task_id} completed successfully")
        update_task(
            task_id,
            TaskStatus.COMPLETED,
            "Transcription completed successfully!",
            progress=100,
            vtt_content=vtt_content
        )
        
    except Exception as e:
        print(f"DEBUG: Task {task_id} failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        update_task(
            task_id,
            TaskStatus.FAILED,
            "Task failed",
            progress=0,
            error=str(e)
        )
    
    finally:
        # Cleanup
        try:
            cleanup_task_files(task_id)
            if gcs_uri:
                await asyncio.to_thread(delete_from_gcs, gcs_uri)
        except Exception:
            pass  # Ignore cleanup errors


async def process_uploaded_file(
    task_id: str,
    file_content: bytes,
    filename: str,
    language_code: str
) -> None:
    """
    Async task to process an uploaded audio file and generate VTT.
    """
    gcs_uri = None
    
    try:
        # Step 1: Save uploaded file
        update_task(
            task_id,
            TaskStatus.PENDING,
            "Saving uploaded file...",
            progress=10
        )
        
        audio_path = await asyncio.to_thread(
            save_uploaded_file, 
            file_content, 
            filename, 
            task_id
        )
        
        # Step 2: Convert to mono 16kHz
        update_task(
            task_id,
            TaskStatus.CONVERTING,
            "Converting audio to mono 16kHz WAV...",
            progress=30
        )
        
        converted_path = await asyncio.to_thread(convert_to_mono_16khz, audio_path, task_id)
        
        # Step 3: Upload to GCS
        update_task(
            task_id,
            TaskStatus.UPLOADING,
            "Uploading audio to Google Cloud Storage...",
            progress=50
        )
        
        gcs_uri = await asyncio.to_thread(upload_to_gcs, converted_path, task_id)
        
        # Step 4: Transcribe using Speech-to-Text V2
        update_task(
            task_id,
            TaskStatus.TRANSCRIBING,
            "Transcribing audio (this may take a while)...",
            progress=70
        )
        
        # Get VTT content directly from STT inline results
        vtt_content = await asyncio.to_thread(
            transcribe_audio,
            gcs_uri,
            task_id,
            language_code
        )
        
        # Save VTT locally
        vtt_local_path = await asyncio.to_thread(save_vtt_locally, task_id, vtt_content)
        
        # Step 5: Complete
        update_task(
            task_id,
            TaskStatus.COMPLETED,
            "Transcription completed successfully!",
            progress=100,
            vtt_content=vtt_content
        )
        
    except Exception as e:
        update_task(
            task_id,
            TaskStatus.FAILED,
            "Task failed",
            progress=0,
            error=str(e)
        )
    
    finally:
        # Cleanup
        try:
            cleanup_task_files(task_id)
            if gcs_uri:
                await asyncio.to_thread(delete_from_gcs, gcs_uri)
        except Exception:
            pass  # Ignore cleanup errors
