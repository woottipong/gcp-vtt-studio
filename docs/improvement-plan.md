# แผนปรับปรุงความแม่นยำในการสร้าง VTT

เอกสารนี้รวบรวมคำแนะนำการปรับปรุงโปรเจ็ค Auto VTT Studio เพื่อเพิ่มความแม่นยำในการสร้าง subtitle

---

## ภาพรวม

ปัจจุบันโปรเจ็คใช้ Google Cloud Speech-to-Text V2 (Chirp 2 model) สำหรับการ transcribe เสียง แต่ยังมีโอกาสปรับปรุงคุณภาพ output ได้อีกมาก

---

## Priority Matrix

| Priority | หัวข้อ | ผลกระทบ | ความยาก |
|----------|--------|---------|---------|
| **สูง** | ใช้ WAV แทน Opus | +20% | ง่าย |
| **สูง** | Audio normalization | +15% | ง่าย |
| **กลาง** | PyThaiNLP tokenization | +10% | ปานกลาง |
| **กลาง** | Denoiser configuration | +5% | ง่าย |
| **ต่ำ** | Custom recognizer | +10% | ปานกลาง |

---

## 1. เปลี่ยนจาก Opus เป็น WAV Format

### ปัจจุบัน
```python
# audio_processor.py - convert_to_opus()
# ใช้ Opus 64kbps ซึ่งเป็น compressed format
'-c:a', 'libopus',
'-b:a', '64k',
```

### ปัญหา
- Opus เป็น lossy format ทำให้สูญเสียข้อมูลเสียงบางส่วน
- สำหรับภาษาไทยที่มีเสียง tonal หลายระดับ ความละเอียดของเสียงสำคัญมาก

### แนวทางแก้ไข

```python
# backend/app/services/audio_processor.py

def convert_to_wav_16khz(input_path: str, task_id: str) -> str:
    """
    Convert audio file to mono 16kHz WAV using FFmpeg.
    Uses uncompressed PCM for maximum quality.
    Returns the path to the converted file.
    """
    temp_dir = ensure_temp_dir()
    output_dir = temp_dir / task_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "audio_mono_16khz.wav"
    
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-acodec', 'pcm_s16le',  # Uncompressed PCM
        '-ac', '1',               # Mono
        '-ar', '16000',           # 16kHz
        '-y',
        str(output_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg conversion failed: {result.stderr}")
    
    return str(output_path)
```

### การแก้ไขใน task_manager.py

```python
# task_manager.py - process_youtube_url() และ process_uploaded_file()

# แทนที่:
upload_path = await asyncio.to_thread(convert_to_opus, audio_path, task_id)

# เป็น:
upload_path = await asyncio.to_thread(convert_to_wav_16khz, audio_path, task_id)
```

---

## 2. เพิ่ม Audio Normalization และ Noise Reduction

### ปัจจุบัน
- ไม่มีการ normalize เสียง
- ไม่มีการลดเสียงรบกวนก่อนส่งให้ STT

### ปัญหา
- เสียงที่ดังหรือเบาเกินไป ทำให้ STT ผิดพลาด
- เสียงรบกวน (background noise) ทำให้คำที่ไม่มีในคำพูดถูก transcribe เข้ามา

### แนวทางแก้ไข

```python
# backend/app/services/audio_processor.py

def enhance_audio(input_path: str, task_id: str) -> str:
    """
    Apply audio enhancement:
    1. Noise reduction (highpass + lowpass filter)
    2. Audio normalization (loudnorm)
    3. Convert to mono 16kHz WAV
    """
    temp_dir = ensure_temp_dir()
    output_dir = temp_dir / task_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "audio_enhanced.wav"
    
    # FFmpeg filters chain:
    # - highpass=f=80: ลดเสียงความถี่ต่ำ (hum, rumble)
    # - lowpass=f=8000: ลดเสียงความถี่สูง (hiss)
    # - loudnorm: normalize เสียงให้คงที่
    #   I=-16: target loudness (industry standard for speech)
    #   TP=-1.5: true peak limit
    #   LRA=11: loudness range
    filter_chain = (
        "highpass=f=80,lowpass=f=8000,"
        "loudnorm=I=-16:TP=-1.5:LRA=11"
    )
    
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-af', filter_chain,
        '-acodec', 'pcm_s16le',
        '-ac', '1',
        '-ar', '16000',
        '-y',
        str(output_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"Audio enhancement failed: {result.stderr}")
    
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"DEBUG: Enhanced audio: {file_size_mb:.1f} MB")
    
    return str(output_path)
```

### การใช้งาน

```python
# task_manager.py - เรียก enhance_audio หลังดาวน์โหลด
audio_path = await asyncio.to_thread(download_youtube_audio, url, task_id)

# เพิ่มขั้นตอน enhance
enhanced_path = await asyncio.to_thread(enhance_audio, audio_path, task_id)

# ใช้ enhanced_path แทน audio_path
gcs_uri = await asyncio.to_thread(upload_to_gcs, enhanced_path, task_id)
```

---

## 3. ปรับปรุง PyThaiNLP Tokenization

### ปัจจุบัน

```python
# gcp_service.py - normalize_thai_spaces()
all_tokens = word_tokenize(joined, engine='newmm')
```

### ปัญหา
- `newmm` (New Maximum Matching) เป็น dictionary-based
- คำที่ไม่อยู่ใน dictionary จะถูกตัดผิด
- ศัพท์เฉพาะทาง, คำใหม่, คำแปลกๆ อาจผิดพลาด

### แนวทางแก้ไข

```python
# backend/app/services/gcp_service.py

from pythainlp.tokenize import word_tokenize, Tokenizer
from pythainlp.corpus import stopwords

# Custom dictionary สำหรับคำที่ต้องการรักษา
CUSTOM_DICTIONARY = {
    'อวัยวะ', 'โควิด', 'วัคซีน', 'เอสเอ็มเอส',
    'พี่น้อง', 'ประเทศ', 'รัฐบาล', 'ฝ่ายค้าน',
    # เพิ่มคำตาม need
}

def normalize_thai_spaces_improved(vtt_text: str) -> str:
    """
    Improved Thai spacing normalization with:
    1. Custom dictionary support
    2. Better handling of mixed language
    3. Alternative tokenization engine
    """
    # ลองใช้ longest matching engine
    all_tokens = word_tokenize(
        joined, 
        engine='longest',  # ลอง engine นี้
        keep_whitespace=False
    )
    
    # หรือสร้าง custom tokenizer
    custom_tokenizer = Tokenizer(CUSTOM_DICTIONARY)
    all_tokens = custom_tokenizer.word_tokenize(joined)
    
    # ... (rest of the code unchanged)
```

---

## 4. ปรับ Denoiser Configuration

### ปัจจุบัน

```python
# gcp_service.py - transcribe_audio()
"denoiser_config": cloud_speech.DenoiserConfig(
    denoise_audio=True,
    snr_threshold=20.0,  # Medium sensitivity
)
```

### ปัญหา
- SNR threshold 20.0 ค่อนข้างสูง อาจตัดคำเสียงเบาๆ ออกไป
- เหมาะสำหรับเสียงที่มี noise ปานกลาง

### แนวทางแก้ไข

```python
# gcp_service.py

# สำหรับเสียงที่ค่อนข้างใส (YouTube คุณภาพสูง)
"denoiser_config": cloud_speech.DenoiserConfig(
    denoise_audio=True,
    snr_threshold=25.0,  # เพิ่มขึ้น = ลด noise น้อยลง = รักษาเสียงเบา
),

# สำหรับเสียงที่มี noise มาก (บันทึกเสียงในห้อง)
"denoiser_config": cloud_speech.DenoiserConfig(
    denoise_audio=True,
    snr_threshold=15.0,  # ลดลง = ลด noise มากขึ้น
),
```

### แนะนำให้ทำเป็น config

```python
# config.py

class Settings(BaseSettings):
    # ...
    denoise_snr_threshold: float = 20.0
    
# .env
DENOISE_SNR_THRESHOLD=20.0
```

---

## 5. สร้าง Custom Recognizer

### ปัจจุบัน

```python
# config.py
stt_recognizer: str = "_"  # ใช้ default recognizer
```

### ปัญหา
- Default recognizer อาจไม่ได้ optimize สำหรับภาษาไทยโดยเฉพาะ

### แนวทางแก้ไข

สร้าง custom recognizer ด้วย Chirp model:

```bash
cd backend
python create_recognizer.py
```

```python
# create_recognizer.py (ปรับปรุง)

from google.cloud import speech_v2 as speech
from google.cloud.speech_v2 import types as cloud_speech
from google.api_core.client_options import ClientOptions
from app.config import get_settings

settings = get_settings()

def create_thai_recognizer():
    """สร้าง recognizer สำหรับภาษาไทย"""
    
    client_options = ClientOptions(
        api_endpoint=f"{settings.google_cloud_location}-speech.googleapis.com"
    )
    
    client = speech.SpeechClient.from_service_account_json(
        settings.google_application_credentials,
        client_options=client_options
    )
    
    parent = f"projects/{settings.google_cloud_project}/locations/{settings.google_cloud_location}"
    
    # สร้าง recognizer ด้วย Chirp model
    recognizer = speech.Recognizer(
        name=f"{parent}/recognizers/chirp-thai-improved",
        model="chirp",  # ใช้ Chirp model
        language_codes=["th-TH"],
        default_recognition_config=speech.RecognitionConfig(
            features=speech.RecognitionFeatures(
                enable_automatic_punctuation=True,
                enable_word_time_offsets=True,
            ),
            # เพิ่ม config เพิ่มเติม
            adaptation=speech.RecognitionAdaptation(
                phrase_sets=[],  # เพิ่ม phrase sets ถ้าต้องการ
            )
        )
    )
    
    operation = client.create_recognizer(
        request={
            "parent": parent,
            "recognizer_id": "chirp-thai-improved",
            "recognizer": recognizer
        }
    )
    
    result = operation.result()
    print(f"Created recognizer: {result.name}")
    
    return result

if __name__ == "__main__":
    create_thai_recognizer()
```

---

## 6. Configuration ที่แนะนำ

### .env

```env
# Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=asia-southeast1
GOOGLE_CLOUD_STORAGE_BUCKET=your-bucket-name

# Speech-to-Text V2
STT_MODEL=chirp
STT_LANGUAGE_CODE=th-TH
STT_RECOGNIZER=chirp-thai-improved

# Audio Processing
AUDIO_CONVERT_TO_WAV=true
AUDIO_NORMALIZE=true
AUDIO_DENOISE=true
DENOISE_SNR_THRESHOLD=20.0

# File Processing
TEMP_DIR=/tmp/auto_vtt_studio
MAX_FILE_SIZE_MB=500

# Timeout
YOUTUBE_DOWNLOAD_TIMEOUT=300
TRANSCRIPTION_TIMEOUT=3600
```

---

## สรุปแผนการปรับปรุง

### Phase 1: Quick Wins (1-2 ชั่วโมง)
- [ ] เปลี่ยนจาก Opus เป็น WAV
- [ ] เพิ่ม audio normalization
- [ ] ปรับ SNR threshold

### Phase 2: Medium Effort (2-4 ชั่วโมง)
- [ ] เพิ่ม noise reduction filter
- [ ] ปรับปรุง PyThaiNLP tokenization
- [ ] สร้าง custom recognizer

### Phase 3: Advanced (1 วัน)
- [ ] เพิ่ม custom dictionary สำหรับคำเฉพาะทาง
- [ ] ทดสอบกับ dataset หลายๆ แบบ
- [ ] ปรับ config ตามผลการทดสอบ

---

## References

- [Google Cloud Speech-to-Text V2 Documentation](https://cloud.google.com/speech-to-text/v2)
- [PyThaiNLP Documentation](https://pythainlp.github.io/docs/3.0/)
- [FFmpeg Audio Filters](https://ffmpeg.org/ffmpeg-filters.html)
- [Loudnorm Filter Explained](https://mediaarea.net/AudioNormalizer)
