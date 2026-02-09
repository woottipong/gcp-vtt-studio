import re
from pydantic import BaseModel, field_validator
from enum import Enum
from typing import Optional


class TaskStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    CONVERTING = "converting"
    UPLOADING = "uploading"
    TRANSCRIBING = "transcribing"
    COMPLETED = "completed"
    FAILED = "failed"


# Regex patterns for YouTube URL validation
YOUTUBE_PATTERNS = [
    r'^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
    r'^https?://(?:www\.)?youtube\.com/embed/[\w-]+',
    r'^https?://youtu\.be/[\w-]+',
    r'^https?://(?:www\.)?youtube\.com/shorts/[\w-]+',
]


class YouTubeRequest(BaseModel):
    url: str
    language_code: str = "th-TH"
    
    @field_validator('url')
    @classmethod
    def validate_youtube_url(cls, v: str) -> str:
        """Validate YouTube URL to prevent injection attacks."""
        v = v.strip()
        
        if not v:
            raise ValueError('URL is required')
        
        # Check URL length to prevent DoS
        if len(v) > 2048:
            raise ValueError('URL too long')
        
        # Validate against YouTube URL patterns
        is_valid = any(re.match(pattern, v) for pattern in YOUTUBE_PATTERNS)
        
        if not is_valid:
            raise ValueError(
                'Invalid YouTube URL. Supported formats: '
                'https://youtube.com/watch?v=VIDEO_ID, '
                'https://youtu.be/VIDEO_ID'
            )
        
        # Additional safety: check for shell injection characters
        dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '{', '}', '<', '>']
        if any(char in v for char in dangerous_chars):
            raise ValueError('Invalid characters in URL')
        
        return v


class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    message: str
    progress: int = 0


class TaskStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    message: str
    progress: int
    vtt_url: Optional[str] = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None
    segments_count: Optional[int] = None
