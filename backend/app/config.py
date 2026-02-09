from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Google Cloud Settings
    google_cloud_project: str
    google_cloud_location: str = "global"
    google_cloud_storage_bucket: str
    google_application_credentials: Optional[str] = None
    
    # Speech-to-Text V2 Settings
    stt_recognizer: str = "_"  # Use "_" for default recognizer
    stt_language_code: str = "th-TH"
    stt_model: str = "long"
    
    # File Processing Settings
    temp_dir: str = "/tmp/auto_vtt_studio"
    vtt_output_dir: str = "./vtt_output"
    max_file_size_mb: int = 500
    
    # Timeout Settings (seconds)
    youtube_download_timeout: int = 300  # 5 minutes
    transcription_timeout: int = 3600  # 1 hour
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
