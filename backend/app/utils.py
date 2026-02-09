"""
Utility functions for Auto VTT Studio.
Contains helper functions for responses, task management, etc.
"""

from typing import Optional
from app.models import TaskResponse, TaskStatus
from app.constants import MSG_TASK_CREATED


def create_task_response(
    task_id: str,
    status: TaskStatus = TaskStatus.PENDING,
    message: str = MSG_TASK_CREATED,
    progress: int = 0
) -> TaskResponse:
    """
    Create a standardized TaskResponse object.
    
    Args:
        task_id: Unique task identifier
        status: Task status (default: PENDING)
        message: Status message (default: "Task created successfully")
        progress: Progress percentage 0-100 (default: 0)
        
    Returns:
        TaskResponse object
    """
    return TaskResponse(
        task_id=task_id,
        status=status,
        message=message,
        progress=progress
    )


def format_vtt_filename(task_id: str) -> str:
    """
    Format VTT filename for download.
    
    Args:
        task_id: Unique task identifier
        
    Returns:
        Formatted filename string
    """
    return f"subtitles_{task_id}.vtt"


def get_vtt_download_url(task_id: str) -> str:
    """
    Generate VTT download URL for a task.
    
    Args:
        task_id: Unique task identifier
        
    Returns:
        Download URL path
    """
    return f"/api/task/{task_id}/download"


def format_file_size(bytes_size: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        bytes_size: File size in bytes
        
    Returns:
        Formatted string (e.g., "15.3 MB", "512.5 KB")
    """
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_size / (1024 * 1024 * 1024):.1f} GB"
