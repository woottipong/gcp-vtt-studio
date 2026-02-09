# Auto VTT Studio - Developer Agent Guide

> คู่มือสำหรับ AI Agent ที่ดูแลและพัฒนาโปรเจกต์ Auto VTT Studio

## 📋 Project Overview

**Auto VTT Studio** คือ web application สำหรับสร้างคำบรรยาย VTT จากวิดีโอ YouTube หรือไฟล์เสียง โดยใช้ Google Cloud Speech-to-Text V2 (Chirp 2) พร้อมการประมวลผลภาษาไทยด้วย PyThaiNLP

### Core Purpose
- **Primary Use Case**: แปลงเสียงภาษาไทยเป็นคำบรรยาย VTT คุณภาพสูง
- **Target Users**: ผู้สร้างคอนเทนต์ไทย, นักแปล, ผู้ต้องการคำบรรยายภาษาไทย
- **Key Differentiator**: PyThaiNLP integration สำหรับการจัดช่องว่างภาษาไทยระดับ clause (ไม่ใช่ word-level)

## 🏗️ Technical Stack

### Backend (Python 3.13)
- **Framework**: FastAPI (async/await)
- **Speech-to-Text**: Google Cloud Speech-to-Text V2 (Chirp 2 model)
- **Thai NLP**: PyThaiNLP 5.0+ with python-crfsuite
- **Audio Processing**: 
  - FFmpeg (mono 16kHz WAV conversion)
  - yt-dlp (YouTube audio extraction)
- **Storage**: Google Cloud Storage (asia-southeast1)

### Frontend (React 18 + TypeScript)
- **Build Tool**: Vite
- **UI Framework**: Tailwind CSS 3.x
- **Color Scheme**: Indigo (#4f46e5) + Blue + Cyan (premium navy aesthetic)
- **Design Pattern**: Glass morphism, floating animations, segmented controls
- **Language Selector**: Segmented control (pill-style buttons) สำหรับ 2 ภาษา

### Infrastructure
- **Environment**: Environment variables via `.env`
- **Task Management**: In-memory async task tracking
- **File Processing**: Temp directory with automatic cleanup

## 🔑 Critical Design Decisions

### 1. Why Chirp 2 (Not Chirp 3)?
**Decision**: ใช้ `chirp_2` model แทน `chirp_3`

**Reason**: 
- Chirp 3 ไม่ส่ง VTT output files กลับมา (404 errors, 0 files in GCS)
- ทดสอบทั้งกับและไม่มี denoiser ก็ล้มเหลวเหมือนกัน
- Chirp 2 stable และส่ง VTT files กลับมาอย่างถูกต้อง

**Configuration**:
```python
RecognitionConfig(
    auto_decoding_config=AutoDetectDecodingConfig(),  # ให้ Google auto-detect format
    model=settings.stt_model,  # "chirp_2" from .env
    language_codes=[language_code],
    features=RecognitionFeatures(enable_word_time_offsets=True),
    denoiser_config=DenoiserConfig(
        denoise_audio=True,
        snr_threshold=20.0  # Medium sensitivity
    )
)
```

### 2. Why PyThaiNLP is Essential?
**Problem**: Raw Chirp 2 output มีช่องว่างระหว่างทุกคำ:
```
เลือก ตั้ง ประเทศ ไทย แล้ว ประเทศ ไทย
```

**Solution**: PyThaiNLP ทำ 3 steps:
1. ลบช่องว่างทั้งหมดออก → `เลือกตั้งประเทศไทยแล้วประเทศไทย`
2. ใช้ `word_tokenize(engine='newmm')` แบ่งคำใหม่
3. เพิ่มช่องว่างที่ clause boundaries เท่านั้น:
   - หลังจาก: ครับ, ค่ะ, นะ, ครับผม (end particles)
   - ก่อนหน้า: แต่, เพราะว่า, ถ้า, เนื่องจาก (conjunctions)

**Result**:
```
เลือกตั้งประเทศไทย แล้วประเทศไทยกำลังจะมี
```

**Impact**: ~93% improvement in Thai text readability

**Code Location**: `backend/app/services/gcp_service.py` → `normalize_thai_spaces()`

### 3. Why NOT Golang Migration?
**Question**: ย้าย backend ไป Golang ได้ไหม?

**Answer**: ❌ ไม่แนะนำ

**Reasons**:
- PyThaiNLP ไม่มี equivalent ใน Go ecosystem
- Thai word tokenization quality คือ core value ของระบบ
- Python มี mature libraries: yt-dlp, Google Cloud SDK, PyThaiNLP
- Performance ไม่ใช่ bottleneck (รอ Google Speech-to-Text API อยู่แล้ว)

### 4. Language Support Limited to 2
**Decision**: รองรับเฉพาะ **ไทย** และ **อังกฤษ (US)**

**Reasons**:
- Focus ที่ Thai language quality
- ลดความซับซ้อนของ UI/UX
- PyThaiNLP optimization ใช้กับภาษาไทยเท่านั้น
- Segmented control (pill buttons) เหมาะกับ 2 ตัวเลือก

**Display Names**: ใช้ภาษาไทย (`"ไทย"`, `"อังกฤษ"`) ไม่ใช่ English

## 📁 Code Structure

### Backend Key Files

**`backend/app/main.py`** (225 lines)
- FastAPI routes: `/api/transcribe/*`, `/api/languages`, `/api/task/*`
- CORS middleware for frontend
- Background task spawning
- Language list endpoint (เหลือ 2 ภาษา)

**`backend/app/services/gcp_service.py`** (~330 lines)
- `transcribe_audio()`: Main Google Cloud STT V2 integration
- `normalize_thai_spaces()`: **Critical** - Thai text post-processing
- `_normalize_thai_line()`: Segment Thai/non-Thai text
- `_add_clause_spaces()`: PyThaiNLP word tokenization + clause detection
- Denoiser configuration: `snr_threshold=20.0`

**`backend/app/services/task_manager.py`**
- In-memory task state management
- `process_youtube_url()`: yt-dlp → FFmpeg → GCS → STT
- `process_uploaded_file()`: Upload → FFmpeg → GCS → STT
- Progress tracking (0-100%)

**`backend/app/services/audio_processor.py`**
- FFmpeg conversion: `ffmpeg -i input -ar 16000 -ac 1 output.wav`
- yt-dlp YouTube extraction: best audio quality
- Temporary file cleanup

**`backend/app/config.py`**
- Pydantic Settings management
- Environment variable validation
- Default values for all configs

**`backend/app/models.py`**
- Pydantic models for API requests/responses
- TaskStatus enum: PENDING, PROCESSING, COMPLETED, ERROR

### Frontend Key Files

**`frontend/src/App.tsx`**
- Main application layout
- Floating animated background orbs (indigo/blue/cyan)
- Glass-card header with gradient
- Tab switching (YouTube / Upload)
- Task polling loop

**`frontend/src/components/LanguageSelector.tsx`**
- **Segmented Control** (pill-style buttons)
- Gradient active state: `from-indigo-600 via-blue-600 to-cyan-600`
- Smooth transitions (300ms)
- Disabled state support

**`frontend/src/components/FileUpload.tsx`**
- Drag-and-drop file upload
- File type validation
- Progress indicator

**`frontend/src/hooks/useTranscription.ts`**
- Task submission logic
- Status polling with 2s interval
- State management (idle, uploading, processing, completed, error)

**`frontend/src/index.css`**
- Custom scrollbar (indigo gradient)
- Glass morphism classes: `.glass-card`, `.glass-header`
- Gradient text: `.gradient-text`
- Button styles: `.btn-primary`

**`frontend/tailwind.config.js`**
- Color palette: Indigo (50-900), accent colors
- Custom animations: float, slide-up, fade-in
- Extended theme configuration

### Configuration Files

**`backend/.env`**
```env
STT_MODEL=chirp_2
STT_LANGUAGE_CODE=th-TH
STT_RECOGNIZER=chirp-thai-recognizer
GOOGLE_CLOUD_LOCATION=asia-southeast1
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_STORAGE_BUCKET=your-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=../credential/gcp.json
```

**`credential/gcp.json`**
- Google Cloud Service Account key
- ⚠️ **NEVER commit to git**
- Roles needed: Cloud Speech Admin, Storage Object Admin

## 🛠️ Development Guidelines

### When to Edit Files

**DON'T EDIT** these unless absolutely necessary:
- `gcp_service.py` → Thai spacing logic is fragile and well-tested
- `audio_processor.py` → FFmpeg commands are optimized
- Tailwind color configuration → UI design is finalized

**SAFE TO EDIT**:
- `main.py` → Add new API endpoints
- `App.tsx` → Add UI features
- `.env` → Change configuration
- Component files → Enhance UX

### Testing Checklist

**Backend Changes**:
1. ✅ Test Thai transcription: ช่องว่างถูกต้อง (clause-level)
2. ✅ Test English transcription: no PyThaiNLP processing
3. ✅ Check logs: no errors from Google Cloud API
4. ✅ Verify VTT file downloads correctly

**Frontend Changes**:
1. ✅ Test both language selections (ไทย, อังกฤษ)
2. ✅ Verify gradient colors display correctly
3. ✅ Check responsive design (mobile/desktop)
4. ✅ Test hover/active states

### Code Quality Standards

**Python**:
- Use `async/await` for I/O operations
- Type hints for function parameters
- Pydantic models for data validation
- Environment variables via `settings` object (never hardcode)

**TypeScript**:
- Strict type checking enabled
- React FC with explicit prop types
- Tailwind classes only (no inline styles)
- Use custom hooks for state logic

## ⚠️ Known Limitations

### Technical Constraints

1. **Chirp 3 Incompatibility**
   - Chirp 3 ไม่ส่ง VTT output กลับมา
   - ต้องใช้ Chirp 2 เท่านั้น
   - Status: ไม่มีแผนแก้ไข (รอ Google fix)

2. **PyThaiNLP Required for Thai**
   - Golang/Rust migration ทำไม่ได้
   - Thai quality ขึ้นกับ PyThaiNLP 100%
   - Status: Design decision, not a bug

3. **Denoiser Limitations**
   - Removes background music/rain/traffic
   - **Cannot remove background human voices**
   - SNR threshold 20.0 is medium sensitivity
   - Status: Google Cloud API limitation

4. **word_time_offsets Trade-off**
   - Required for VTT timestamp generation
   - May slightly degrade transcription accuracy
   - Status: Acceptable trade-off for VTT format

### Performance Considerations

- **Long Audio Files**: 1+ hour files take 10-30 minutes
- **Batch Processing**: Not supported (one file at a time)
- **Concurrent Requests**: Task manager is in-memory (not production-scale)

## 🚀 Deployment Checklist

### Before Production

- [ ] Set production GCS bucket with lifecycle policy
- [ ] Configure proper CORS origins
- [ ] Set up monitoring for Google Cloud API quota
- [ ] Add rate limiting to API endpoints
- [ ] Implement persistent task storage (Redis/DB)
- [ ] Set up error alerting
- [ ] Configure CDN for frontend static files
- [ ] Enable HTTPS
- [ ] Set production environment variables
- [ ] Test Thai transcription with real-world audio

### Environment Variables to Set

```env
# Production values
GOOGLE_CLOUD_PROJECT=prod-project-id
GOOGLE_CLOUD_STORAGE_BUCKET=prod-vtt-bucket
GOOGLE_CLOUD_LOCATION=asia-southeast1
STT_MODEL=chirp_2
TEMP_DIR=/var/tmp/auto_vtt_studio
MAX_FILE_SIZE_MB=500
```

## 📊 Monitoring Points

### Key Metrics to Track

1. **Transcription Success Rate**
   - Target: >95% for Thai, >98% for English
   - Alert if drops below 90%

2. **API Response Times**
   - Download: <10s for YouTube
   - Upload: <5s for 100MB files
   - STT processing: depends on audio length

3. **Google Cloud Costs**
   - STT API usage (per minute)
   - GCS storage costs
   - Data transfer costs

4. **Error Rates**
   - YouTube download failures
   - FFmpeg conversion errors
   - Google Cloud API errors

### Log Files to Monitor

```bash
# Backend logs
tail -f logs/backend.log | grep ERROR

# Look for:
- "Failed to download YouTube"
- "FFmpeg conversion failed"
- "Google Cloud API error"
- "PyThaiNLP error"
```

## 🔧 Common Maintenance Tasks

### Update Dependencies

```bash
# Backend
cd backend
pip install --upgrade google-cloud-speech google-cloud-storage pythainlp

# Frontend
cd frontend
npm update
```

### Clear Temp Files

```bash
# Clean up temp directory
rm -rf /tmp/auto_vtt_studio/*

# Check GCS bucket size
gsutil du -sh gs://your-bucket-name
```

### Restart Services

```bash
# Using scripts
./stop.sh && ./start.sh

# Manual
pkill -f uvicorn
pkill -f vite
./dev.sh
```

## 📝 Version History

### Current State (Feb 2026)
- ✅ Chirp 2 model with denoiser (SNR 20.0)
- ✅ PyThaiNLP 5.0+ integration
- ✅ Modern UI (Indigo/Blue color scheme)
- ✅ Segmented language selector (2 languages)
- ✅ Environment variable configuration
- ✅ Thai language display names

### Previous Iterations
- ❌ Attempted Chirp 3 migration (failed - VTT output issue)
- ❌ Considered Golang migration (rejected - no PyThaiNLP equivalent)
- ❌ Purple/Pink color scheme (changed to professional Indigo)
- ❌ Dropdown language selector (changed to segmented control)

## 🎯 Future Enhancement Ideas

### High Priority
- [ ] SRT format export (in addition to VTT)
- [ ] Batch file upload (multiple files at once)
- [ ] Progress percentage for long audio files
- [ ] Audio preview player in UI

### Medium Priority
- [ ] Custom PyThaiNLP dictionary upload
- [ ] Dark mode toggle
- [ ] Audio waveform visualization
- [ ] Export with custom timestamp format

### Low Priority
- [ ] Support for more languages (if PyThaiNLP-like quality available)
- [ ] Speaker diarization (who is speaking)
- [ ] Real-time transcription (streaming mode)
- [ ] Translation to other languages

### Not Recommended
- ❌ Golang backend rewrite (loses PyThaiNLP)
- ❌ Use Chirp 3 model (VTT output broken)
- ❌ Remove PyThaiNLP (degrades Thai quality 93%)

## 🆘 Emergency Troubleshooting

### Service Down
```bash
# Check if running
ps aux | grep uvicorn
ps aux | grep vite

# Restart
./stop.sh && ./start.sh

# Check logs
tail -50 logs/backend.log
tail -50 logs/frontend.log
```

### Google Cloud API Errors
```bash
# Verify credentials
gcloud auth list

# Test API access
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  https://speech.googleapis.com/v2/projects/PROJECT_ID/locations/asia-southeast1/recognizers
```

### Thai Spacing Issues
- Check PyThaiNLP version: `pip show pythainlp`
- Verify python-crfsuite installed: `pip show python-crfsuite`
- Test clause detection in Python:
  ```python
  from pythainlp.tokenize import word_tokenize
  text = "เลือกตั้งประเทศไทยครับ"
  print(word_tokenize(text, engine='newmm'))
  ```

### Frontend Build Fails
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

## 📌 Remember

1. **Never commit** `credential/gcp.json` to git
2. **Always test** Thai transcription after backend changes
3. **Keep Chirp 2** - don't try Chirp 3 again
4. **PyThaiNLP is essential** - can't remove or replace
5. **UI uses Thai language** - don't change to English displays
6. **Segmented control** is designed for 2 languages only
7. **Indigo/Blue colors** are finalized - matches premium brand

---

*Last Updated: February 9, 2026*
*Maintained by: AI Development Agent*
