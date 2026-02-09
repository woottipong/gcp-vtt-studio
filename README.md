# Auto VTT Studio

A web application for generating VTT subtitles from YouTube URLs or audio files using Google Cloud Speech-to-Text V2.

![Auto VTT Studio](https://img.shields.io/badge/Speech--to--Text-V2-blue)
![React](https://img.shields.io/badge/React-18-61dafb)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688)
![Python](https://img.shields.io/badge/Python-3.11+-3776ab)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- 🎬 **YouTube Support**: Paste any YouTube URL to extract and transcribe audio
- 📁 **Audio File Upload**: Support for WAV, MP3, FLAC, OGG, M4A, AAC, WMA formats
- �🇭 **Thai Language Optimized**: Advanced PyThaiNLP integration for proper Thai spacing and clause detection
- 🌐 **Multi-language**: Support for Thai and English (US)
- 🎨 **Modern UI**: Premium indigo/blue design with glass morphism and smooth animations
- ⚡ **Real-time Progress**: Track transcription progress with live updates
- 📥 **VTT Export**: Download subtitles in WebVTT format
- 🔊 **Audio Denoising**: Built-in noise reduction for better transcription quality

## Architecture

```
auto_vtt_studio/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── main.py            # FastAPI application
│   │   ├── config.py          # Configuration settings
│   │   ├── models.py          # Pydantic models
│   │   └── services/
│   │       ├── audio_processor.py  # yt-dlp & FFmpeg integration
│   │       ├── gcp_service.py      # Google Cloud STT V2 & GCS
│   │       └── task_manager.py     # Async task management
│   ├── requirements.txt
│   └── .env.example
├── frontend/                   # React Vite frontend
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api.ts             # API client
│   │   ├── components/        # UI components
│   │   └── hooks/             # Custom hooks
│   ├── package.json
│   └── tailwind.config.js
└── README.md
```

## Prerequisites

- **Python 3.13+**
- **Node.js 18+**
- **FFmpeg** (for audio conversion)
- **yt-dlp** (installed via pip)
- **PyThaiNLP 5.0+** (for Thai text processing)
- **Google Cloud Platform** account with:
  - Speech-to-Text V2 API enabled (Chirp 2 model)
  - Cloud Storage bucket (asia-southeast1 recommended)
  - Service Account with appropriate permissions

## Google Cloud Setup

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your **Project ID**

### 2. Enable Required APIs

Enable the following APIs in your project:

- **Cloud Speech-to-Text API**
- **Cloud Storage API**

```bash
gcloud services enable speech.googleapis.com
gcloud services enable storage.googleapis.com
```

### 3. Create a Cloud Storage Bucket

```bash
# Create a bucket (choose a globally unique name)
gsutil mb -p YOUR_PROJECT_ID -l us-central1 gs://your-bucket-name

# Set lifecycle policy to auto-delete old files (optional)
gsutil lifecycle set lifecycle.json gs://your-bucket-name
```

### 4. Create a Service Account

1. Go to **IAM & Admin** > **Service Accounts**
2. Click **Create Service Account**
3. Name: `auto-vtt-studio-sa`
4. Grant the following roles:
   - **Cloud Speech Administrator** (or `roles/speech.admin`)
   - **Storage Object Admin** (or `roles/storage.objectAdmin`)
5. Click **Done**

### 5. Download Service Account Key

1. Click on the created service account
2. Go to **Keys** tab
3. Click **Add Key** > **Create new key**
4. Choose **JSON** format
5. Download and save the file securely (e.g., `service-account.json`)

> ⚠️ **Security Warning**: Never commit this file to version control!

### 6. Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
cd backend
cp .env.example .env
```

Edit `.env` with your values:

```env
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=asia-southeast1
GOOGLE_CLOUD_STORAGE_BUCKET=your-bucket-name

# Path to service account JSON file
GOOGLE_APPLICATION_CREDENTIALS=../credential/gcp.json

# Speech-to-Text V2 Configuration
STT_MODEL=chirp_2
STT_LANGUAGE_CODE=th-TH
STT_RECOGNIZER=chirp-thai-recognizer

# File Processing
TEMP_DIR=/tmp/auto_vtt_studio
MAX_FILE_SIZE_MB=500
```

## Quick Start

The easiest way to start the application is using the provided scripts:

### 🚀 Start Both Services (Background Mode)

```bash
./start.sh
```

This will:
- ✓ Check and install dependencies automatically
- ✓ Start backend on http://localhost:8000
- ✓ Start frontend on http://localhost:5173
- ✓ Run both services in background
- ✓ Save logs to `logs/` directory

### 🛑 Stop Services

```bash
./stop.sh
```

### 👨‍💻 Development Mode (Foreground)

```bash
./dev.sh
```

Runs both services in foreground with live output. Press `Ctrl+C` to stop.

---

## Manual Installation

If you prefer to run services manually:

### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install FFmpeg (macOS)
brew install ffmpeg

# Install FFmpeg (Ubuntu/Debian)
sudo apt update && sudo apt install ffmpeg
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

### Start Backend Manually

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend Manually

```bash
cd frontend
npm run dev
```

## Access the Application

- 🌐 **Frontend**: http://localhost:5173
- 🔌 **Backend API**: http://localhost:8000
- 📚 **API Documentation**: http://localhost:8000/docs

## View Logs

When using `start.sh`, logs are saved to:

```bash
# Backend logs
tail -f logs/backend.log

# Frontend logs
tail -f logs/frontend.log
```

## API Endpoints

| Method | Endpoint                       | Description                 |
| ------ | ------------------------------ | --------------------------- |
| `GET`  | `/`                            | Health check                |
| `GET`  | `/api/languages`               | Get supported languages     |
| `POST` | `/api/transcribe/youtube`      | Start YouTube transcription |
| `POST` | `/api/transcribe/upload`       | Start file transcription    |
| `GET`  | `/api/task/{task_id}`          | Get task status             |
| `GET`  | `/api/task/{task_id}/download` | Download VTT file           |

### Example: Transcribe YouTube Video

```bash
curl -X POST http://localhost:8000/api/transcribe/youtube \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID", "language_code": "th-TH"}'
```

### Example: Upload Audio File

```bash
curl -X POST http://localhost:8000/api/transcribe/upload \
  -F "file=@/path/to/audio.mp3" \
  -F "language_code=th-TH"
```

## Supported Languages

| Code    | Language      |
| ------- | ------------- |
| `th-TH` | ไทย (default) |
| `en-US` | อังกฤษ         |

## Production Deployment

### Build Frontend

```bash
cd frontend
npm run build
```

The build output will be in `frontend/dist/`.

### Deploy with Docker (Optional)

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}
      - GOOGLE_CLOUD_STORAGE_BUCKET=${GOOGLE_CLOUD_STORAGE_BUCKET}
    volumes:
      - ./service-account.json:/app/service-account.json:ro
    env_file:
      - .env

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

## How It Works

1. **Upload/YouTube URL** → User provides audio source
2. **Download & Convert** → Extract audio with yt-dlp, convert to mono 16kHz WAV with FFmpeg
3. **Upload to GCS** → Audio file uploaded to Google Cloud Storage
4. **Transcribe** → Google Cloud Speech-to-Text V2 (Chirp 2) generates VTT subtitles with:
   - Auto-detection of audio format
   - Denoiser with SNR threshold 20.0 for noise reduction
   - Word-level timestamps for VTT format
5. **Thai Text Processing** → PyThaiNLP normalizes Thai spacing:
   - Removes word-level spaces from raw output
   - Re-adds spaces at clause boundaries
   - Detects clause markers (ครับ, ค่ะ, นะ) and conjunctions
6. **Download** → User downloads the VTT file with professional Thai formatting

> **Note**: PyThaiNLP is critical for Thai transcription quality, improving readability from word-spaced "เลือก ตั้ง" to natural "เลือกตั้ง แล้วประเทศไทย".

## Project Structure

```
auto_vtt_studio/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI routes
│   │   ├── config.py            # Settings management
│   │   ├── models.py            # Pydantic models
│   │   └── services/
│   │       ├── audio_processor.py   # yt-dlp & FFmpeg
│   │       ├── gcp_service.py       # Google Cloud STT V2
│   │       └── task_manager.py      # Async tasks
│   ├── requirements.txt
│   ├── .env.example
│   └── venv/
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Main application
│   │   ├── api.ts               # Backend API client
│   │   ├── components/          # React components
│   │   └── hooks/               # Custom hooks
│   ├── package.json
│   └── node_modules/
├── credential/
│   └── stt-google.json          # Service account key
├── logs/                        # Application logs
├── start.sh                     # Start services
├── stop.sh                      # Stop services
├── dev.sh                       # Development mode
└── README.md
```

## Troubleshooting

### Common Issues

1. **FFmpeg not found**
   ```bash
   # Verify FFmpeg is installed
   ffmpeg -version
   
   # Install on macOS
   brew install ffmpeg
   
   # Install on Ubuntu/Debian
   sudo apt update && sudo apt install ffmpeg
   ```

2. **Google Cloud authentication error**
   ```bash
   # Verify service account
   gcloud auth activate-service-account --key-file=/path/to/service-account.json
   
   # Check .env file configuration
   cat backend/.env
   ```

3. **Speech-to-Text quota exceeded**
   - Check your API quotas in Google Cloud Console
   - Request quota increase if needed
   - Verify billing is enabled

4. **Long transcription times**
   - Speech-to-Text V2 Batch API processes audio asynchronously
   - Long audio files (>1 hour) may take 10-30 minutes
   - Check logs for progress: `tail -f logs/backend.log`

5. **Port already in use**
   ```bash
   # Check what's using the port
   lsof -i :8000
   lsof -i :5173
   
   # Use stop.sh to clean up
   ./stop.sh
   ```

6. **Dependencies not found**
   ```bash
   # Reinstall backend dependencies
   cd backend
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Reinstall frontend dependencies
   cd frontend
   npm install
   ```

### Logs

Backend logs are printed to stdout. For production, view logs at:

```bash
# When using start.sh
tail -f logs/backend.log
tail -f logs/frontend.log

# Or use Python logging
import logging
logging.basicConfig(level=logging.INFO)
```

## License

MIT License - feel free to use this project for any purpose.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
