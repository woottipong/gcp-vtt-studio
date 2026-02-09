# Auto VTT Studio — Google STT V2 Batch API (VTT Generation)

## กระบวนการสร้าง VTT จาก Google Cloud Speech-to-Text V2

เอกสารนี้อธิบายรายละเอียดเชิงลึกว่า Google Cloud STT V2 Batch API สร้างไฟล์ VTT ได้อย่างไร และโปรเจกต์นี้ใช้งานอย่างไร

---

## 1. Overview

Google Cloud Speech-to-Text V2 มีความสามารถในการ **สร้างไฟล์ VTT (WebVTT) โดยตรง** ผ่าน `VttOutputFileFormatConfig` โดยไม่ต้องเขียน logic แปลง transcript เป็น subtitle format เอง

```
Audio File (GCS) ──► STT V2 Batch API ──► VTT File (GCS)
                         │
                         ├── Transcription (เสียง → ข้อความ)
                         ├── Word Time Offsets (timestamp ทุกคำ)
                         ├── Cue Segmentation (แบ่ง subtitle blocks)
                         └── VTT Formatting (จัดรูปแบบ WebVTT)
```

---

## 2. Request Configuration

### 2.1 RecognitionConfig

```python
config = cloud_speech.RecognitionConfig(
    auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
    language_codes=["th-TH"],
    features=cloud_speech.RecognitionFeatures(
        enable_word_time_offsets=True,
    ),
)
```

| Parameter                  | Value                        | Purpose                              |
| -------------------------- | ---------------------------- | ------------------------------------ |
| `auto_decoding_config`     | `AutoDetectDecodingConfig()` | ให้ Google ตรวจจับ encoding อัตโนมัติ     |
| `language_codes`           | `["th-TH"]`                  | ภาษาที่ต้องการถอดเสียง                   |
| `enable_word_time_offsets` | `True`                       | ให้ timestamp ของแต่ละคำ (จำเป็นสำหรับ VTT) |

### 2.2 RecognitionOutputConfig

```python
output_config = cloud_speech.RecognitionOutputConfig(
    gcs_output_config=cloud_speech.GcsOutputConfig(
        uri="gs://bucket/vtt/task-id/",
    ),
    output_format_config=cloud_speech.OutputFormatConfig(
        vtt=cloud_speech.VttOutputFileFormatConfig(),
    ),
)
```

| Parameter              | Value                             | Purpose                     |
| ---------------------- | --------------------------------- | --------------------------- |
| `gcs_output_config`    | GCS URI prefix                    | ตำแหน่งที่จะเขียนไฟล์ VTT บน GCS  |
| `output_format_config` | `vtt=VttOutputFileFormatConfig()` | สั่งให้ Google สร้าง VTT format |

### 2.3 BatchRecognizeRequest

```python
request = cloud_speech.BatchRecognizeRequest(
    recognizer="projects/.../locations/.../recognizers/chirp-thai-recognizer",
    config=config,
    files=[cloud_speech.BatchRecognizeFileMetadata(uri="gs://bucket/audio/task-id/audio.wav")],
    recognition_output_config=output_config,
)
```

---

## 3. Recognizer Setup

โปรเจกต์นี้ใช้ **Chirp model** ซึ่งเป็น multilingual model ล่าสุดของ Google:

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

**สร้าง Recognizer:**
```bash
python create_recognizer.py
# สร้าง recognizer "chirp-thai-recognizer" ใน asia-southeast1
```

**ทำไมต้องใช้ custom recognizer?**
- ตั้งค่า model เป็น `chirp` (ดีกว่า default model สำหรับภาษาไทย)
- เปิด automatic punctuation + word time offsets เป็น default
- บังคับ region เป็น `asia-southeast1` (ใกล้ Thailand, latency ต่ำ)

---

## 4. Batch API Execution Flow

```
Client ──► batch_recognize(request)
               │
               ▼
           Google Cloud
           ┌────────────────────────────────────────┐
           │  1. รับไฟล์เสียงจาก GCS                  │
           │  2. Decode audio (auto-detect format)    │
           │  3. Run speech recognition (Chirp model) │
           │  4. Generate word-level timestamps       │
           │  5. Segment into subtitle cues           │
           │  6. Format as WebVTT                     │
           │  7. Write VTT file to GCS output path    │
           └────────────────────┬───────────────────┘
                                │
                                ▼
           Operation (Long-Running)
               │
               ▼
           operation.result(timeout=3600)
               │
               ▼
           BatchRecognizeResponse
           └── results[uri]
               └── cloud_storage_result
                   └── vtt_format_uri  ←── "gs://bucket/vtt/task-id/audio_mono_16khz_0.vtt"
```

### Timing

| ความยาวเสียง | เวลาประมวลผลโดยประมาณ |
| ----------- | --------------------- |
| 1-5 นาที     | 30 วินาที - 2 นาที       |
| 5-15 นาที    | 2-5 นาที               |
| 15-60 นาที   | 5-15 นาที              |
| 1-3 ชั่วโมง   | 10-30 นาที             |

> **Note**: Batch API เป็น asynchronous — ไม่ต้อง maintain connection ระหว่างรอ

---

## 5. VTT Output Format

### ตัวอย่าง VTT ที่ Google สร้าง (ก่อน clean)

```vtt
WEBVTT

00:00:00.000 --> 00:00:03.520
สวัสดี ครับ วัน นี้ เรา จะ มา พูด เรื่อง

00:00:03.520 --> 00:00:07.200
การ ใช้ งาน Google Cloud Speech to Text

00:00:07.200 --> 00:00:11.840
ซึ่ง เป็น บริการ ของ Google สำหรับ แปลง เสียง เป็น ข้อ ความ
```

### ตัวอย่าง VTT หลัง `clean_thai_spaces()` (ส่งให้ user)

```vtt
WEBVTT

00:00:00.000 --> 00:00:03.520
สวัสดีครับวันนี้เราจะมาพูดเรื่อง

00:00:03.520 --> 00:00:07.200
การใช้งาน Google Cloud Speech to Text

00:00:07.200 --> 00:00:11.840
ซึ่งเป็นบริการของ Google สำหรับแปลงเสียงเป็นข้อความ
```

### Thai Space Cleaning Logic

```python
def clean_thai_spaces(text: str) -> str:
    # Thai Unicode Range: \u0E00 - \u0E7F
    # ลบ space ระหว่าง Thai characters เท่านั้น
    # ไม่ลบ space ระหว่าง Thai กับ English
    return re.sub(r'(?<=[\u0e00-\u0e7f])\s+(?=[\u0e00-\u0e7f])', '', text)
```

**ทำไมต้องทำ?**
- Google STT V2 tokenize ภาษาไทยแบบเว้นวรรคทุกคำ
- ภาษาไทยปกติเขียนติดกัน ไม่เว้นวรรค
- Regex: ลบ space ที่อยู่ระหว่าง Thai characters สองตัว
- ไม่กระทบ space ระหว่าง Thai-English (เช่น "ใช้งาน Google" ยังมี space)

---

## 6. Response Handling

```python
result = operation.result(timeout=settings.transcription_timeout)

if result.results:
    for uri, file_result in result.results.items():
        # Primary: VTT format URI
        vtt_uri = file_result.cloud_storage_result.vtt_format_uri
        
        # Fallback 1: Native format URI
        native_uri = file_result.cloud_storage_result.native_format_uri
        
        # Fallback 2: Legacy URI
        legacy_uri = file_result.uri
```

**Response Structure:**

```
BatchRecognizeResponse
├── results: Dict[str, BatchRecognizeFileResult]
│   └── "gs://bucket/audio/task-id/audio.wav"
│       └── cloud_storage_result: CloudStorageResult
│           ├── vtt_format_uri: "gs://bucket/vtt/task-id/audio_0.vtt"  ← ใช้ตัวนี้
│           └── native_format_uri: "gs://bucket/vtt/task-id/audio_0.json"
└── total_billed_duration: Duration
```

---

## 7. Error Handling

| Error Type                   | Cause                        | Handling                         |
| ---------------------------- | ---------------------------- | -------------------------------- |
| `TimeoutError`               | Transcription > 3600 seconds | Cancel operation, raise error    |
| `google.api_core.exceptions` | Auth/permission/quota issues | Propagate to task_manager        |
| `RuntimeError`               | No results in response       | "No transcription results found" |
| `ValueError`                 | Invalid GCS URI              | "Invalid GCS URI"                |

### Timeout Flow

```python
try:
    result = operation.result(timeout=3600)
except Exception as e:
    operation.cancel()  # Cancel ongoing operation
    raise TimeoutError(...)
```

---

## 8. GCS File Lifecycle

```
Timeline ──────────────────────────────────────────────────────►

1. Upload audio
   gs://bucket/audio/<task_id>/audio_mono_16khz.wav  ── CREATED

2. STT Batch API runs
   gs://bucket/vtt/<task_id>/audio_mono_16khz_0.vtt  ── CREATED (by Google)

3. Download VTT content to memory
   (Read from GCS → clean_thai_spaces → store in tasks dict)

4. Cleanup
   gs://bucket/audio/<task_id>/audio_mono_16khz.wav  ── DELETED ✓
   gs://bucket/vtt/<task_id>/audio_mono_16khz_0.vtt  ── REMAINS (not auto-deleted)
```

---

## 9. Supported Output Formats

STT V2 Batch API รองรับ output formats ดังนี้:

| Format  | Config Class                | File Extension | ใช้ในโปรเจกต์ |
| ------- | --------------------------- | -------------- | ----------- |
| **VTT** | `VttOutputFileFormatConfig` | `.vtt`         | ✅ ใช้        |
| SRT     | `SrtOutputFileFormatConfig` | `.srt`         | ❌           |
| Native  | (default, no config needed) | `.json`        | ❌           |

ราคาเท่ากันทุก format — เป็นแค่การเลือกรูปแบบผลลัพธ์

---

## 10. WebVTT Format Specification

```vtt
WEBVTT                              ← Required header

                                    ← Blank line separator

00:00:00.000 --> 00:00:03.520       ← Timestamp (HH:MM:SS.mmm)
สวัสดีครับวันนี้เราจะมาพูดเรื่อง      ← Subtitle text

00:00:03.520 --> 00:00:07.200       ← Next cue
การใช้งาน Google Cloud
```

**Key Points:**
- Header `WEBVTT` คือบรรทัดแรกเสมอ
- Timestamp format: `HH:MM:SS.mmm --> HH:MM:SS.mmm`
- แต่ละ cue คั่นด้วยบรรทัดว่าง
- Google จัดการ cue segmentation อัตโนมัติ (ไม่ต้อง configure)
- File encoding: UTF-8
