import os
import subprocess
import uuid
import shutil
import signal
from pathlib import Path
from typing import Any
import yt_dlp  # type: ignore
from app.config import get_settings

settings = get_settings()


class TimeoutException(Exception):
    """Raised when an operation times out."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutException("Operation timed out")


def ensure_temp_dir() -> Path:
    """Ensure the temporary directory exists."""
    temp_path = Path(settings.temp_dir)
    temp_path.mkdir(parents=True, exist_ok=True)
    return temp_path


# Formats that Chirp 2 auto_decoding_config supports natively
CHIRP2_SUPPORTED_FORMATS = {'.wav', '.mp3', '.flac', '.ogg', '.opus', '.webm', '.m4a', '.aac'}


def is_chirp2_compatible(file_path: str) -> bool:
    """Check if a file format is natively supported by Chirp 2 auto_decoding_config."""
    ext = Path(file_path).suffix.lower()
    return ext in CHIRP2_SUPPORTED_FORMATS


def download_youtube_audio(url: str, task_id: str) -> str:
    """
    Download audio from YouTube URL using yt-dlp.
    Downloads as OGG/Opus directly (YouTube's native audio format) to avoid
    unnecessary WAV conversion. Chirp 2's auto_decoding_config handles decoding.
    Returns the path to the downloaded audio file.
    """
    temp_dir = ensure_temp_dir()
    output_path = temp_dir / task_id
    output_path.mkdir(parents=True, exist_ok=True)
    
    output_template = str(output_path / "audio.%(ext)s")
    
    ydl_opts: Any = {
        'format': 'bestaudio[ext=webm]/bestaudio/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'extract_audio': True,
        'js_runtimes': {'node': {}},
        'remote_components': ['ejs:github'],
        'socket_timeout': settings.youtube_download_timeout,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'opus',
        }],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        raise RuntimeError(f"Failed to download YouTube audio: {str(e)}")
    
    # Find the downloaded audio file (opus/ogg/webm)
    audio_files = (
        list(output_path.glob("*.opus")) or
        list(output_path.glob("*.ogg")) or
        list(output_path.glob("*.webm")) or
        list(output_path.glob("*.m4a")) or
        list(output_path.glob("*.mp3")) or
        list(output_path.glob("*.wav"))
    )
    if not audio_files:
        raise FileNotFoundError("Failed to download audio from YouTube")
    
    downloaded = str(audio_files[0])
    file_size_mb = Path(downloaded).stat().st_size / (1024 * 1024)
    print(f"DEBUG: Downloaded audio: {Path(downloaded).name} ({file_size_mb:.1f} MB)")
    
    return downloaded


def convert_to_opus(input_path: str, task_id: str) -> str:
    """
    Convert audio file to OGG/Opus (compressed, small file size).
    Opus is optimal for speech and produces very small files.
    Chirp 2's auto_decoding_config handles decoding natively.
    Returns the path to the converted file.
    """
    temp_dir = ensure_temp_dir()
    output_dir = temp_dir / task_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "audio_converted.opus"
    
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-ac', '1',           # Mono
        '-ar', '16000',       # 16kHz (Opus supports this natively)
        '-c:a', 'libopus',
        '-b:a', '64k',        # 64kbps is plenty for speech
        '-application', 'voip',  # Optimized for speech
        '-y',
        str(output_path)
    ]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg Opus conversion failed: {result.stderr}")
    
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"DEBUG: Converted to Opus: {file_size_mb:.1f} MB")
    
    return str(output_path)


def convert_to_mono_16khz(input_path: str, task_id: str) -> str:
    """
    Convert audio file to mono 16kHz WAV using FFmpeg.
    Fallback for formats that need explicit conversion.
    Returns the path to the converted file.
    """
    temp_dir = ensure_temp_dir()
    output_dir = temp_dir / task_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "audio_mono_16khz.wav"
    
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-acodec', 'pcm_s16le',
        '-ac', '1',  # Mono
        '-ar', '16000',  # 16kHz
        '-y',  # Overwrite output
        str(output_path)
    ]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg conversion failed: {result.stderr}")
    
    return str(output_path)


def save_uploaded_file(file_content: bytes, filename: str, task_id: str) -> str:
    """
    Save an uploaded audio file to the temp directory.
    Returns the path to the saved file.
    """
    temp_dir = ensure_temp_dir()
    output_dir = temp_dir / task_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Sanitize filename
    safe_filename = "".join(c for c in filename if c.isalnum() or c in ".-_")
    output_path = output_dir / safe_filename
    
    with open(output_path, 'wb') as f:
        f.write(file_content)
    
    return str(output_path)


def cleanup_task_files(task_id: str) -> None:
    """Clean up temporary files for a task."""
    temp_dir = ensure_temp_dir()
    task_dir = temp_dir / task_id
    
    if task_dir.exists():
        shutil.rmtree(task_dir)


def generate_task_id() -> str:
    """Generate a unique task ID."""
    return str(uuid.uuid4())
