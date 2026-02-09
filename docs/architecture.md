# Auto VTT Studio — Architecture Document

## Overview

Auto VTT Studio เป็น Web Application สำหรับสร้างไฟล์ Subtitle รูปแบบ WebVTT จาก YouTube URL หรือไฟล์เสียง โดยใช้ **Google Cloud Speech-to-Text V2 Batch API** เป็นตัวประมวลผลหลัก

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client (Browser)                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              React + Vite + TailwindCSS                      │   │
│  │  ┌──────────┐ ┌────────────┐ ┌──────────────────────────┐   │   │
│  │  │FileUpload│ │LanguageSelect│ │  ProgressIndicator      │   │   │
│  │  └─────┬────┘ └──────┬─────┘ └────────────┬─────────────┘   │   │
│  │        │              │                    │                  │   │
│  │        └──────────────┼────────────────────┘                  │   │
│  │                       ▼                                       │   │
│  │            useTranscription Hook                              │   │
│  │                       │                                       │   │
│  │                       ▼                                       │   │
│  │              api.ts (Axios Client)                            │   │
│  └───────────────────────┬──────────────────────────────────────┘   │
└──────────────────────────┼──────────────────────────────────────────┘
                           │ HTTP (REST API)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI + Python)                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  main.py — FastAPI Application                               │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐     │   │
│  │  │ /transcribe│  │ /task/:id  │  │ /task/:id/download │     │   │
│  │  │  /youtube  │  │  (status)  │  │     (VTT file)     │     │   │
│  │  │  /upload   │  │            │  │                    │     │   │
│  │  └─────┬──────┘  └─────┬──────┘  └────────┬───────────┘     │   │
│  │        │               │                   │                 │   │
│  │        ▼               ▼                   ▼                 │   │
│  │  ┌──────────────────────────────────────────────────────┐    │   │
│  │  │           task_manager.py (Background Tasks)         │    │   │
│  │  │  - In-memory task storage (Dict)                     │    │   │
│  │  │  - Async task orchestration                          │    │   │
│  │  │  - Progress tracking & status updates                │    │   │
│  │  └─────────────┬───────────────────┬────────────────────┘    │   │
│  │                │                   │                         │   │
│  │                ▼                   ▼                         │   │
│  │  ┌──────────────────┐  ┌──────────────────────────────┐     │   │
│  │  │audio_processor.py│  │     gcp_service.py           │     │   │
│  │  │ - yt-dlp download│  │ - GCS upload/download        │     │   │
│  │  │ - FFmpeg convert │  │ - STT V2 Batch Recognize     │     │   │
│  │  │ - File management│  │ - VTT content retrieval      │     │   │
│  │  └──────────────────┘  │ - Thai text post-processing  │     │   │
│  │                        └──────────────┬───────────────┘     │   │
│  └───────────────────────────────────────┼─────────────────────┘   │
└──────────────────────────────────────────┼─────────────────────────┘
                                           │ gRPC / REST
                                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Google Cloud Platform                             │
│  ┌──────────────────────┐    ┌──────────────────────────────────┐   │
│  │  Cloud Storage (GCS) │    │  Speech-to-Text V2 (Batch API)  │   │
│  │  ┌────────────────┐  │    │  ┌────────────────────────────┐ │   │
│  │  │ audio/<task_id>/│──┼───►│  │ BatchRecognizeRequest      │ │   │
│  │  │  audio.wav      │  │    │  │ - AutoDetectDecodingConfig │ │   │
│  │  └────────────────┘  │    │  │ - language_codes            │ │   │
│  │  ┌────────────────┐  │◄───┼──│ - enable_word_time_offsets │ │   │
│  │  │ vtt/<task_id>/  │  │    │  │ - VttOutputFileFormat      │ │   │
│  │  │  subtitle.vtt   │  │    │  └────────────────────────────┘ │   │
│  │  └────────────────┘  │    │                                  │   │
│  └──────────────────────┘    └──────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Frontend

| Technology  | Version | Purpose                 |
| ----------- | ------- | ----------------------- |
| React       | 18      | UI Framework            |
| TypeScript  | -       | Type-safe JavaScript    |
| Vite        | -       | Build tool & dev server |
| TailwindCSS | -       | Utility-first CSS       |
| Axios       | -       | HTTP client             |

### Backend

| Technology           | Version | Purpose                      |
| -------------------- | ------- | ---------------------------- |
| Python               | 3.11+   | Runtime                      |
| FastAPI              | ≥0.109  | Web framework                |
| Uvicorn              | ≥0.27   | ASGI server                  |
| yt-dlp               | latest  | YouTube audio download       |
| FFmpeg               | -       | Audio format conversion      |
| google-cloud-speech  | ≥2.24   | Speech-to-Text V2 API client |
| google-cloud-storage | ≥2.14   | Cloud Storage client         |
| Pydantic             | ≥2.6    | Data validation & settings   |

### Google Cloud Services

| Service           | Purpose                                 |
| ----------------- | --------------------------------------- |
| Cloud Storage     | Temporary storage for audio & VTT files |
| Speech-to-Text V2 | Audio transcription with VTT output     |
| Service Account   | Authentication for GCP API access       |

---

## Module Responsibilities

### `main.py` — API Layer

- FastAPI application instance & CORS configuration
- Route handlers for transcription endpoints
- Request validation & response formatting
- Background task delegation

### `config.py` — Configuration Management

- Environment variable loading via Pydantic Settings
- GCP project, bucket, and recognizer configuration
- Timeout and file size limits
- Singleton pattern with `@lru_cache`

### `models.py` — Data Models

- `TaskStatus` enum: pending → downloading → converting → uploading → transcribing → completed/failed
- `YouTubeRequest`: URL validation with regex patterns and injection prevention
- `TaskResponse` / `TaskStatusResponse`: API response schemas

### `audio_processor.py` — Audio Processing

- **YouTube download**: `yt-dlp` with WAV post-processing, signal-based timeout
- **Audio conversion**: FFmpeg → mono channel, 16kHz, PCM 16-bit LE
- **File management**: temp directory, file saving, cleanup

### `gcp_service.py` — Google Cloud Integration

- **Storage Client**: Singleton, upload/download/delete on GCS
- **Speech Client**: Singleton, regional endpoint configuration
- **BatchRecognize**: VTT output format config, word time offsets
- **Thai text cleaning**: Remove extra spaces between Thai characters via regex

### `task_manager.py` — Task Orchestration

- **In-memory task store**: Python dict (not persistent)
- **Pipeline orchestration**: coordinates 5-step processing pipeline
- **Async execution**: `asyncio.to_thread()` for blocking I/O
- **Cleanup**: auto-delete temp files and GCS audio after completion

---

## Data Flow

### Input → Output Pipeline

```
User Input (YouTube URL or Audio File)
        │
        ▼
┌─ Step 1: Acquire Audio ─────────────────────┐
│  YouTube: yt-dlp download → WAV             │
│  Upload: save to /tmp/auto_vtt_studio/      │
│  Progress: 10%                              │
└──────────────────────┬──────────────────────┘
                       ▼
┌─ Step 2: Convert Audio ─────────────────────┐
│  FFmpeg: → mono, 16kHz, PCM 16-bit WAV      │
│  Progress: 30%                              │
└──────────────────────┬──────────────────────┘
                       ▼
┌─ Step 3: Upload to GCS ─────────────────────┐
│  gs://<bucket>/audio/<task_id>/audio.wav     │
│  Progress: 50%                               │
└──────────────────────┬───────────────────────┘
                       ▼
┌─ Step 4: Google STT V2 Batch API ────────────┐
│  BatchRecognizeRequest:                       │
│    - recognizer: chirp-thai-recognizer        │
│    - input: gs://...audio.wav                │
│    - output: gs://<bucket>/vtt/<task_id>/     │
│    - format: VttOutputFileFormatConfig        │
│  Progress: 70%                               │
└──────────────────────┬───────────────────────┘
                       ▼
┌─ Step 5: Retrieve & Clean VTT ──────────────┐
│  Download VTT from GCS                       │
│  clean_thai_spaces() → Remove extra spaces   │
│  Store in memory, return to user             │
│  Progress: 100%                              │
└──────────────────────┬───────────────────────┘
                       ▼
┌─ Cleanup ────────────────────────────────────┐
│  Delete temp files from /tmp/                │
│  Delete audio file from GCS                  │
│  (VTT file remains on GCS)                   │
└──────────────────────────────────────────────┘
```

---

## Task State Machine

```
                    ┌──────────┐
          ┌────────►│  FAILED  │
          │         └──────────┘
          │              ▲
          │              │ (any error)
          │              │
┌─────────┴──┐    ┌──────┴──────┐    ┌───────────┐    ┌───────────┐    ┌──────────────┐    ┌───────────┐
│   PENDING  │───►│ DOWNLOADING │───►│CONVERTING │───►│ UPLOADING │───►│ TRANSCRIBING │───►│ COMPLETED │
│  (0-10%)   │    │   (10%)     │    │  (30%)    │    │  (50%)    │    │   (70%)      │    │  (100%)   │
└────────────┘    └─────────────┘    └───────────┘    └───────────┘    └──────────────┘    └───────────┘
```

---

## Authentication Model

```
Service Account JSON (credential/gcp.json)
        │
        ├──► google.cloud.storage.Client.from_service_account_json()
        │           → Upload/download audio & VTT files
        │
        └──► google.cloud.speech_v2.SpeechClient.from_service_account_json()
                    → BatchRecognize API calls
```

**Required IAM Roles:**

- `roles/speech.admin` — Speech-to-Text API access
- `roles/storage.objectAdmin` — GCS read/write/delete

---

## Recognizer Configuration

โปรเจกต์นี้ใช้ **Chirp model** สำหรับ Thai transcription:

```python
# create_recognizer.py
recognizer = speech_v2.Recognizer(
    model="chirp",
    language_codes=["th-TH"],
    default_recognition_config=speech_v2.RecognitionConfig(
        features=speech_v2.RecognitionFeatures(
            enable_automatic_punctuation=True,
            enable_word_time_offsets=True,
        )
    )
)
```

- **Model**: `chirp` (Google's latest multilingual model)
- **Location**: `asia-southeast1` (closest to Thailand)
- **Recognizer ID**: `chirp-thai-recognizer`

---

## Security Considerations

1. **YouTube URL Validation**: Regex pattern matching + dangerous character blocking (`;`, `&`, `|`, `` ` ``, `$`, etc.)
2. **File Upload Validation**: Extension whitelist (`.wav`, `.mp3`, `.flac`, `.ogg`, `.m4a`, `.aac`, `.wma`) + size limit (500MB)
3. **Service Account**: JSON key file stored outside version control in `credential/`
4. **CORS**: Restricted to `localhost:5173` and `localhost:3000`
5. **Timeout Protection**: Configurable timeouts for YouTube download (5 min) and transcription (1 hour)

---

## Limitations & Trade-offs

| Item            | Current Implementation        | Production Recommendation             |
| --------------- | ----------------------------- | ------------------------------------- |
| Task Storage    | In-memory Python dict         | Redis / PostgreSQL                    |
| File Storage    | Local /tmp directory          | Persistent volume / direct GCS        |
| Concurrency     | FastAPI BackgroundTasks       | Celery / Cloud Tasks                  |
| Authentication  | None (open API)               | JWT / API Key                         |
| VTT Persistence | Remains on GCS after download | Auto-cleanup with TTL                 |
| Monitoring      | print() statements            | Structured logging + Cloud Monitoring |
