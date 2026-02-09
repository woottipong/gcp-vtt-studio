# Auto VTT Studio — API Reference

## Base URL

```
http://localhost:8000
```

---

## Endpoints

### 1. Health Check

```
GET /
```

**Response** `200 OK`

```json
{
    "status": "ok",
    "message": "Auto VTT Studio API is running"
}
```

---

### 2. Get Supported Languages

```
GET /api/languages
```

**Response** `200 OK`

```json
{
    "languages": [
        { "code": "th-TH", "name": "Thai" },
        { "code": "en-US", "name": "English (US)" },
        { "code": "en-GB", "name": "English (UK)" },
        { "code": "zh-CN", "name": "Chinese (Simplified)" },
        { "code": "ja-JP", "name": "Japanese" },
        { "code": "ko-KR", "name": "Korean" },
        { "code": "vi-VN", "name": "Vietnamese" },
        { "code": "id-ID", "name": "Indonesian" },
        { "code": "ms-MY", "name": "Malay" },
        { "code": "de-DE", "name": "German" },
        { "code": "fr-FR", "name": "French" },
        { "code": "es-ES", "name": "Spanish" },
        { "code": "pt-BR", "name": "Portuguese (Brazil)" }
    ],
    "default": "th-TH"
}
```

---

### 3. Transcribe YouTube Video

```
POST /api/transcribe/youtube
```

**Request Body** `application/json`

| Field           | Type   | Required | Default | Description          |
| --------------- | ------ | -------- | ------- | -------------------- |
| `url`           | string | ✅        | -       | YouTube URL          |
| `language_code` | string | ❌        | `th-TH` | Language BCP-47 code |

**Supported YouTube URL Formats:**
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtube.com/embed/VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/shorts/VIDEO_ID`

**Example Request:**

```bash
curl -X POST http://localhost:8000/api/transcribe/youtube \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "language_code": "th-TH"
  }'
```

**Response** `200 OK`

```json
{
    "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "pending",
    "message": "Task created successfully",
    "progress": 0
}
```

**Error Responses:**

| Status | Description                             |
| ------ | --------------------------------------- |
| `422`  | Invalid YouTube URL or validation error |

**URL Validation Rules:**
- Must match one of the supported YouTube URL patterns
- Maximum length: 2048 characters
- Dangerous characters blocked: `;`, `&`, `|`, `` ` ``, `$`, `(`, `)`, `{`, `}`, `<`, `>`

---

### 4. Transcribe Uploaded Audio File

```
POST /api/transcribe/upload
```

**Request Body** `multipart/form-data`

| Field           | Type   | Required | Default | Description          |
| --------------- | ------ | -------- | ------- | -------------------- |
| `file`          | file   | ✅        | -       | Audio file           |
| `language_code` | string | ❌        | `th-TH` | Language BCP-47 code |

**Supported Audio Formats:**
- `.wav` — WAV (PCM)
- `.mp3` — MP3
- `.flac` — FLAC
- `.ogg` — OGG Vorbis
- `.m4a` — MPEG-4 Audio
- `.aac` — AAC
- `.wma` — Windows Media Audio

**Maximum File Size:** 500 MB (configurable via `MAX_FILE_SIZE_MB`)

**Example Request:**

```bash
curl -X POST http://localhost:8000/api/transcribe/upload \
  -F "file=@/path/to/audio.mp3" \
  -F "language_code=th-TH"
```

**Response** `200 OK`

```json
{
    "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "pending",
    "message": "Task created successfully",
    "progress": 0
}
```

**Error Responses:**

| Status | Description              |
| ------ | ------------------------ |
| `400`  | No filename provided     |
| `400`  | Unsupported file format  |
| `400`  | File too large (> 500MB) |

---

### 5. Get Task Status

```
GET /api/task/{task_id}
```

**Path Parameters:**

| Parameter | Type   | Description      |
| --------- | ------ | ---------------- |
| `task_id` | string | UUID of the task |

**Example Request:**

```bash
curl http://localhost:8000/api/task/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Response** `200 OK`

```json
{
    "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "transcribing",
    "message": "Transcribing audio (this may take a while)...",
    "progress": 70,
    "vtt_url": null,
    "error": null
}
```

**Response when completed:**

```json
{
    "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "completed",
    "message": "Transcription completed successfully!",
    "progress": 100,
    "vtt_url": "/api/task/a1b2c3d4-e5f6-7890-abcd-ef1234567890/download",
    "error": null
}
```

**Response when failed:**

```json
{
    "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "failed",
    "message": "Task failed",
    "progress": 0,
    "vtt_url": null,
    "error": "Transcription timed out after 3600 seconds"
}
```

**Task Status Values:**

| Status         | Progress | Description                       |
| -------------- | -------- | --------------------------------- |
| `pending`      | 0-10%    | Task created, waiting to start    |
| `downloading`  | 10%      | Downloading audio from YouTube    |
| `converting`   | 30%      | Converting to mono 16kHz WAV      |
| `uploading`    | 50%      | Uploading to Google Cloud Storage |
| `transcribing` | 70%      | Google STT V2 processing audio    |
| `completed`    | 100%     | VTT file ready for download       |
| `failed`       | 0%       | Error occurred during processing  |

**Error Responses:**

| Status | Description    |
| ------ | -------------- |
| `404`  | Task not found |

---

### 6. Download VTT File

```
GET /api/task/{task_id}/download
```

**Path Parameters:**

| Parameter | Type   | Description      |
| --------- | ------ | ---------------- |
| `task_id` | string | UUID of the task |

**Example Request:**

```bash
curl -O http://localhost:8000/api/task/a1b2c3d4-e5f6-7890-abcd-ef1234567890/download
```

**Response** `200 OK`

```
Content-Type: text/vtt
Content-Disposition: attachment; filename=subtitles_a1b2c3d4-e5f6-7890-abcd-ef1234567890.vtt
```

**VTT Content Example:**

```vtt
WEBVTT

00:00:00.000 --> 00:00:03.500
สวัสดีครับวันนี้เราจะมาพูดเรื่อง

00:00:03.500 --> 00:00:07.200
การใช้งาน Google Cloud Speech-to-Text
```

**Error Responses:**

| Status | Description            |
| ------ | ---------------------- |
| `400`  | Task not completed yet |
| `404`  | Task not found         |
| `404`  | VTT content not found  |

---

## Frontend API Client

Frontend ใช้ Axios client ที่ proxy ผ่าน Vite dev server:

```typescript
// api.ts
const API_BASE_URL = '/api';

export const api = {
    getLanguages():           GET  /api/languages
    transcribeYouTube(url):   POST /api/transcribe/youtube
    transcribeUpload(file):   POST /api/transcribe/upload
    getTaskStatus(taskId):    GET  /api/task/{taskId}
    downloadVtt(taskId):      GET  /api/task/{taskId}/download
};
```

**Polling Behavior:**
- Frontend polls `GET /api/task/{task_id}` every **2 seconds**
- Stops polling when status is `completed` or `failed`

---

## Configuration Reference

Backend configuration via environment variables (`.env` file):

| Variable                         | Default                | Description                         |
| -------------------------------- | ---------------------- | ----------------------------------- |
| `GOOGLE_CLOUD_PROJECT`           | *required*             | GCP Project ID                      |
| `GOOGLE_CLOUD_LOCATION`          | `global`               | GCP region (e.g. `asia-southeast1`) |
| `GOOGLE_CLOUD_STORAGE_BUCKET`    | *required*             | GCS bucket name                     |
| `GOOGLE_APPLICATION_CREDENTIALS` | `None`                 | Path to service account JSON        |
| `STT_RECOGNIZER`                 | `_`                    | Recognizer ID (`_` = default)       |
| `STT_LANGUAGE_CODE`              | `th-TH`                | Default language code               |
| `STT_MODEL`                      | `long`                 | STT model type                      |
| `TEMP_DIR`                       | `/tmp/auto_vtt_studio` | Temporary file directory            |
| `MAX_FILE_SIZE_MB`               | `500`                  | Maximum upload file size in MB      |
| `YOUTUBE_DOWNLOAD_TIMEOUT`       | `300`                  | YouTube download timeout (seconds)  |
| `TRANSCRIPTION_TIMEOUT`          | `3600`                 | Transcription timeout (seconds)     |

---

## Error Handling

All error responses follow the FastAPI standard format:

```json
{
    "detail": "Error description message"
}
```

**Common Error Scenarios:**

| Scenario                  | HTTP Status | Detail Message                                |
| ------------------------- | ----------- | --------------------------------------------- |
| Invalid YouTube URL       | `422`       | `Invalid YouTube URL. Supported formats: ...` |
| Unsupported file format   | `400`       | `Unsupported file format. Allowed: ...`       |
| File too large            | `400`       | `File too large. Maximum size: 500MB`         |
| Task not found            | `404`       | `Task not found`                              |
| Task not completed        | `400`       | `Task not completed yet`                      |
| Google Cloud auth failure | `500`       | Internal server error (check logs)            |
| Transcription timeout     | `500`       | Stored in task error field                    |
