import asyncio
import os
import re
from pathlib import Path
from typing import Dict, Optional, Tuple
from app.models import TaskStatus
from app.config import get_settings
from app.services.audio_processor import (
    download_youtube_audio,
    convert_to_opus,
    convert_to_mono_16khz,
    save_uploaded_file,
    cleanup_task_files,
    is_chirp2_compatible,
)
from app.services.gcp_service import (
    upload_to_gcs,
    transcribe_audio,
    delete_from_gcs,
)

# In-memory task storage (use Redis or database in production)
tasks: Dict[str, dict] = {}

settings = get_settings()


def parse_vtt_metrics(vtt_content: str) -> Tuple[float, int]:
    """Parse VTT content to get duration in seconds and number of segments."""
    segments = 0
    max_time = 0.0
    
    # Match VTT timestamp lines
    timestamp_re = re.compile(r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})')
    
    for line in vtt_content.split('\n'):
        match = timestamp_re.search(line)
        if match:
            segments += 1
            end_time_str = match.group(2)
            # Convert HH:MM:SS.mmm to seconds
            try:
                h, m, s = end_time_str.split(':')
                seconds = int(h) * 3600 + int(m) * 60 + float(s)
                if seconds > max_time:
                    max_time = seconds
            except (ValueError, IndexError):
                continue
                
    return max_time, segments


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
    duration_seconds: Optional[float] = None,
    segments_count: Optional[int] = None,
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
        "duration_seconds": duration_seconds,
        "segments_count": segments_count,
    })


async def _cleanup_resources(task_id: str, gcs_uri: Optional[str]) -> None:
    """
    Fire-and-forget cleanup of temp files and GCS objects.
    Runs asynchronously after task completion so user sees results immediately.
    """
    try:
        cleanup_task_files(task_id)
    except Exception as e:
        print(f"Warning: Failed to cleanup local files for {task_id}: {e}")
    
    try:
        if gcs_uri:
            await asyncio.to_thread(delete_from_gcs, gcs_uri)
    except Exception as e:
        print(f"Warning: Failed to cleanup GCS for {task_id}: {e}")


async def process_youtube_url(task_id: str, url: str, language_code: str) -> None:
    """
    Async task to process a YouTube URL and generate VTT.
    Optimized: downloads as Opus (YouTube's native format) and uploads
    directly to GCS without WAV conversion.
    """
    gcs_uri = None
    
    try:
        # Step 1: Download audio from YouTube (as Opus — no WAV conversion)
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
        
        # Log audio duration for debugging
        try:
            import subprocess as _sp
            probe = _sp.run(
                ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', audio_path],
                capture_output=True, text=True
            )
            if probe.returncode == 0:
                dur = float(probe.stdout.strip())
                print(f"DEBUG: Audio duration: {dur:.1f}s ({dur/60:.1f} min)")
        except Exception:
            pass
        
        # Step 2: Upload directly to GCS (skip WAV conversion — Chirp 2 auto-decodes)
        update_task(
            task_id,
            TaskStatus.UPLOADING,
            "Uploading audio to Google Cloud Storage...",
            progress=40
        )
        
        gcs_uri = await asyncio.to_thread(upload_to_gcs, audio_path, task_id)
        
        # Step 3: Transcribe using Speech-to-Text V2
        update_task(
            task_id,
            TaskStatus.TRANSCRIBING,
            "Transcribing audio (this may take a while)...",
            progress=60
        )
        
        vtt_content = await asyncio.to_thread(
            transcribe_audio, 
            gcs_uri, 
            task_id,
            language_code
        )
        
        # Save VTT locally
        await asyncio.to_thread(save_vtt_locally, task_id, vtt_content)
        
        # Parse metrics
        duration, segments = parse_vtt_metrics(vtt_content)
        
        # Step 4: Complete — mark done BEFORE cleanup so user sees result immediately
        print(f"DEBUG: Task {task_id} completed successfully")
        update_task(
            task_id,
            TaskStatus.COMPLETED,
            "Transcription completed successfully!",
            progress=100,
            vtt_content=vtt_content,
            duration_seconds=duration,
            segments_count=segments
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
        # Fire-and-forget cleanup — don't block the completed status
        asyncio.ensure_future(_cleanup_resources(task_id, gcs_uri))


async def process_uploaded_file(
    task_id: str,
    file_content: bytes,
    filename: str,
    language_code: str
) -> None:
    """
    Async task to process an uploaded audio file and generate VTT.
    Optimized: if file is already Chirp 2 compatible, skip conversion.
    Otherwise converts to Opus for smaller upload size.
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
        
        # Step 2: Convert if needed (skip if already compatible)
        upload_path = audio_path
        if is_chirp2_compatible(audio_path):
            print(f"DEBUG: File {filename} is Chirp 2 compatible, skipping conversion")
            update_task(
                task_id,
                TaskStatus.CONVERTING,
                "Audio format compatible, skipping conversion...",
                progress=30
            )
        else:
            update_task(
                task_id,
                TaskStatus.CONVERTING,
                "Converting audio to Opus...",
                progress=30
            )
            upload_path = await asyncio.to_thread(convert_to_opus, audio_path, task_id)
        
        # Step 3: Upload to GCS
        update_task(
            task_id,
            TaskStatus.UPLOADING,
            "Uploading audio to Google Cloud Storage...",
            progress=50
        )
        
        gcs_uri = await asyncio.to_thread(upload_to_gcs, upload_path, task_id)
        
        # Step 4: Transcribe using Speech-to-Text V2
        update_task(
            task_id,
            TaskStatus.TRANSCRIBING,
            "Transcribing audio (this may take a while)...",
            progress=70
        )
        
        vtt_content = await asyncio.to_thread(
            transcribe_audio,
            gcs_uri,
            task_id,
            language_code
        )
        
        # Save VTT locally
        await asyncio.to_thread(save_vtt_locally, task_id, vtt_content)
        
        # Parse metrics
        duration, segments = parse_vtt_metrics(vtt_content)
        
        # Step 5: Complete — mark done BEFORE cleanup so user sees result immediately
        update_task(
            task_id,
            TaskStatus.COMPLETED,
            "Transcription completed successfully!",
            progress=100,
            vtt_content=vtt_content,
            duration_seconds=duration,
            segments_count=segments
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
        # Fire-and-forget cleanup — don't block the completed status
        asyncio.ensure_future(_cleanup_resources(task_id, gcs_uri))
