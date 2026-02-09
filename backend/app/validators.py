"""
Validators for Auto VTT Studio.
Contains validation logic for inputs, files, and formats.
"""

from typing import Optional
from fastapi import HTTPException
from app.constants import (
    ALLOWED_AUDIO_EXTENSIONS,
    BYTES_PER_MB,
    HTTP_400_BAD_REQUEST,
    MSG_NO_FILENAME,
    MSG_UNSUPPORTED_FORMAT,
    MSG_FILE_TOO_LARGE,
)


def validate_filename(filename: Optional[str]) -> str:
    """
    Validate that a filename is provided.
    
    Args:
        filename: The filename to validate
        
    Returns:
        The validated filename
        
    Raises:
        HTTPException: If filename is None or empty
    """
    if not filename:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=MSG_NO_FILENAME
        )
    return filename


def get_file_extension(filename: str) -> str:
    """
    Extract and normalize file extension from filename.
    
    Args:
        filename: The filename to extract extension from
        
    Returns:
        Lowercase file extension with leading dot (e.g., '.mp3')
        Empty string if no extension found
    """
    if '.' not in filename:
        return ''
    return '.' + filename.split('.')[-1].lower()


def validate_audio_format(filename: str) -> str:
    """
    Validate that the audio file format is supported.
    
    Args:
        filename: The filename to check
        
    Returns:
        The file extension if valid
        
    Raises:
        HTTPException: If format is not supported
    """
    file_ext = get_file_extension(filename)
    
    if file_ext not in ALLOWED_AUDIO_EXTENSIONS:
        formats = ', '.join(sorted(ALLOWED_AUDIO_EXTENSIONS))
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=MSG_UNSUPPORTED_FORMAT.format(formats=formats)
        )
    
    return file_ext


def validate_file_size(file_content: bytes, max_size_mb: int) -> float:
    """
    Validate that file size is within limits.
    
    Args:
        file_content: The file content bytes
        max_size_mb: Maximum allowed size in MB
        
    Returns:
        File size in MB
        
    Raises:
        HTTPException: If file exceeds maximum size
    """
    file_size_mb = len(file_content) / BYTES_PER_MB
    
    if file_size_mb > max_size_mb:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=MSG_FILE_TOO_LARGE.format(max_size=max_size_mb)
        )
    
    return file_size_mb


def validate_uploaded_file(
    filename: Optional[str],
    file_content: bytes,
    max_size_mb: int
) -> tuple[str, str, float]:
    """
    Comprehensive validation for uploaded audio files.
    
    Args:
        filename: Name of the uploaded file
        file_content: The file content bytes
        max_size_mb: Maximum allowed size in MB
        
    Returns:
        Tuple of (validated_filename, file_extension, file_size_mb)
        
    Raises:
        HTTPException: If any validation fails
    """
    validated_filename = validate_filename(filename)
    file_ext = validate_audio_format(validated_filename)
    file_size_mb = validate_file_size(file_content, max_size_mb)
    
    return validated_filename, file_ext, file_size_mb
