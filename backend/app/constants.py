"""
Backend constants for Auto VTT Studio.
Centralized location for all constant values.
"""

from typing import Final, Set

# Audio file formats
ALLOWED_AUDIO_EXTENSIONS: Final[Set[str]] = {
    '.wav',
    '.mp3', 
    '.flac',
    '.ogg',
    '.m4a',
    '.aac',
    '.wma'
}

# MIME types mapping
AUDIO_MIME_TYPES: Final[dict[str, str]] = {
    '.wav': 'audio/wav',
    '.mp3': 'audio/mpeg',
    '.flac': 'audio/flac',
    '.ogg': 'audio/ogg',
    '.m4a': 'audio/mp4',
    '.aac': 'audio/aac',
    '.wma': 'audio/x-ms-wma'
}

# Supported languages
SUPPORTED_LANGUAGES: Final[list[dict[str, str]]] = [
    {"code": "th-TH", "name": "ไทย"},
    {"code": "en-US", "name": "อังกฤษ"},
]

DEFAULT_LANGUAGE: Final[str] = "th-TH"

# API endpoints
API_PREFIX: Final[str] = "/api"

# Response messages
MSG_TASK_CREATED: Final[str] = "Task created successfully"
MSG_TASK_NOT_FOUND: Final[str] = "Task not found"
MSG_TASK_NOT_COMPLETED: Final[str] = "Task not completed yet"
MSG_VTT_NOT_FOUND: Final[str] = "VTT content not found"
MSG_NO_FILENAME: Final[str] = "No filename provided"
MSG_UNSUPPORTED_FORMAT: Final[str] = "Unsupported file format. Allowed: {formats}"
MSG_FILE_TOO_LARGE: Final[str] = "File too large. Maximum size: {max_size}MB"

# Task status messages
MSG_TASK_PENDING: Final[str] = "Task created, starting download..."
MSG_TASK_PROCESSING: Final[str] = "Task created, processing file..."

# HTTP Status Codes
HTTP_400_BAD_REQUEST: Final[int] = 400
HTTP_404_NOT_FOUND: Final[int] = 404

# File size conversions
BYTES_PER_MB: Final[int] = 1024 * 1024

# CORS origins
CORS_ORIGINS: Final[list[str]] = [
    "http://localhost:5173",
    "http://localhost:3000",
]
