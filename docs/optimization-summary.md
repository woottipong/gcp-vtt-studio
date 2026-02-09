# Backend Optimization Summary

## Overview

สรุปการ optimize backend pipeline ของ Auto VTT Studio เพื่อให้ประมวลผลต่อคลิปได้เร็วขึ้น รวม 6 improvements + 1 UX enhancement

---

## Optimization #1: Skip WAV Conversion (YouTube Pipeline)

**ปัญหาเดิม:** yt-dlp ดาวน์โหลดเสียงจาก YouTube แล้วแปลงเป็น WAV (uncompressed) ก่อนส่งไป Google STT

**สิ่งที่เปลี่ยน:**
- ดาวน์โหลดเป็น **Opus** โดยตรง (YouTube เก็บเสียงเป็น Opus อยู่แล้ว)
- ใช้ `preferredcodec: 'opus'` และ `format: 'bestaudio[ext=webm]/bestaudio/best'`
- Chirp 2 รองรับ Opus ผ่าน `auto_decoding_config` ไม่ต้องแปลง

**ผลลัพธ์:**
- ลดเวลา FFmpeg conversion ลง ~10-30 วินาที (ขึ้นกับความยาวคลิป)
- ลดขนาดไฟล์ที่อัพโหลด: WAV 10 นาที ≈ 100MB → Opus ≈ 5MB

**ไฟล์ที่เปลี่ยน:** `audio_processor.py` → `download_youtube_audio()`

---

## Optimization #2: Upload Compressed Format to GCS

**ปัญหาเดิม:** อัพโหลดไฟล์ WAV (uncompressed) ขึ้น GCS → ใช้เวลาอัพโหลดนาน + เสีย GCS storage cost

**สิ่งที่เปลี่ยน:**
- YouTube pipeline: อัพโหลด Opus ตรง (จาก Opt #1)
- Upload pipeline: ถ้าไฟล์ที่ user อัพโหลดเป็น format ที่ Chirp 2 รองรับ → ข้ามการแปลง, ถ้าไม่รองรับ → แปลงเป็น Opus (ไม่ใช่ WAV)
- เพิ่มฟังก์ชัน `convert_to_opus()` — Mono 16kHz, 64kbps, voip mode
- เพิ่มฟังก์ชัน `is_chirp2_compatible()` — check supported formats

**Chirp 2 Supported Formats:**
```python
CHIRP2_SUPPORTED_FORMATS = {'.wav', '.mp3', '.flac', '.ogg', '.opus', '.webm', '.m4a', '.aac'}
```

**ผลลัพธ์:**
- ลดเวลาอัพโหลด GCS ลง 5-20x (ขึ้นกับขนาดไฟล์)
- ลด GCS storage cost

**ไฟล์ที่เปลี่ยน:** `audio_processor.py` → `convert_to_opus()`, `is_chirp2_compatible()`; `task_manager.py` → ทั้งสอง pipeline

---

## Optimization #3: Fire-and-Forget GCS Cleanup

**ปัญหาเดิม:** หลัง transcription เสร็จ ต้องรอลบไฟล์จาก GCS + local temp ก่อน user จะเห็นผลลัพธ์

**สิ่งที่เปลี่ยน:**
- Mark task เป็น `COMPLETED` **ก่อน** cleanup
- ใช้ `asyncio.ensure_future(_cleanup_resources())` ทำ cleanup แบบ fire-and-forget
- เพิ่ม `_cleanup_resources()` helper จัดการ error silently

**Code Pattern:**
```python
# Mark done BEFORE cleanup so user sees result immediately
update_task(task_id, TaskStatus.COMPLETED, ...)

# Fire-and-forget cleanup in finally block
asyncio.ensure_future(_cleanup_resources(task_id, gcs_uri))
```

**ผลลัพธ์:**
- User เห็นผลลัพธ์เร็วขึ้น ~1-3 วินาที (ไม่ต้องรอ GCS delete)

**ไฟล์ที่เปลี่ยน:** `task_manager.py` → `_cleanup_resources()`, ทั้งสอง pipeline

---

## Optimization #4: Batch PyThaiNLP Tokenization

**ปัญหาเดิม:** เรียก `word_tokenize()` ทีละบรรทัดของ subtitle — เรียกซ้ำ 100+ ครั้งต่อไฟล์ มี overhead จาก dictionary loading ทุกครั้ง

**สิ่งที่เปลี่ยน:**
- รวม Thai text จากทุกบรรทัด → join ด้วย Zero-Width Space (`\u200b`) → tokenize ครั้งเดียว → split กลับ
- 3-pass algorithm:
  1. **Collect:** เก็บ text lines และ indices
  2. **Batch tokenize:** join + `word_tokenize()` ครั้งเดียว + split by separator
  3. **Rebuild:** ใส่ clause spacing กลับทีละบรรทัด

**Code Pattern:**
```python
_SEP = '\u200b'  # Zero-width space
joined = _SEP.join(all_thai_parts)
all_tokens = word_tokenize(joined, engine='newmm')  # ONE call
# Split tokens back by separator
```

**ผลลัพธ์:**
- ลดเวลา normalization จาก ~2-5 วินาที → ~0.5-1 วินาที (100+ calls → 1 call)

**ไฟล์ที่เปลี่ยน:** `gcp_service.py` → `normalize_thai_spaces()`

---

## Optimization #5: Skip Conversion for Compatible Uploads

**ปัญหาเดิม:** ทุกไฟล์ที่ user อัพโหลดจะถูกแปลงเป็น WAV ก่อนเสมอ แม้ว่า format นั้น Chirp 2 จะรองรับอยู่แล้ว

**สิ่งที่เปลี่ยน:**
- เช็ค `is_chirp2_compatible(audio_path)` ก่อน convert
- ถ้า compatible → อัพโหลดตรงไป GCS เลย
- ถ้าไม่ compatible → convert เป็น Opus (ไม่ใช่ WAV)

**Code Pattern:**
```python
if is_chirp2_compatible(audio_path):
    print("File is Chirp 2 compatible, skipping conversion")
    upload_path = audio_path
else:
    upload_path = convert_to_opus(audio_path, task_id)
```

**ผลลัพธ์:**
- ไฟล์ MP3/FLAC/OGG/M4A ที่ user อัพโหลดไม่ต้องแปลง → ประหยัดเวลา 5-15 วินาที

**ไฟล์ที่เปลี่ยน:** `task_manager.py` → `process_uploaded_file()`

---

## UX Enhancement: Granular Progress Reporting

**ปัญหาเดิม:** ระหว่าง Google transcribe (60-100%) user เห็นแค่ "Transcribing..." นานหลายนาทีโดยไม่รู้ว่าเกิดอะไรขึ้น

**สิ่งที่เปลี่ยน:**
- เพิ่ม `progress_callback` parameter ใน `transcribe_audio()`
- Poll `operation.metadata.transcription_metadata.progress_percent` ทุก 3 วินาที
- Map Google's 0-100% → App's 60-96% range พร้อมข้อความ descriptive

**Progress Mapping:**

| App Progress | ข้อความที่ user เห็น               | แหล่งที่มา                         |
| ------------ | ------------------------------ | ------------------------------- |
| 60%          | Queued for transcription...    | Hardcoded — ก่อน Google เริ่ม      |
| 60-66%       | Decoding audio...              | Google metadata (0-20%)         |
| 66-75%       | Recognizing speech... (X%)     | Google metadata (20-50%)        |
| 75-84%       | Generating subtitles... (X%)   | Google metadata (50-80%)        |
| 84-90%       | Finalizing results... (X%)     | Google metadata (80-100%)       |
| 90%          | Downloading subtitles...       | Hardcoded — อ่าน VTT จาก GCS     |
| 93%          | Normalizing Thai text...       | Hardcoded — PyThaiNLP normalize |
| 96%          | Cleaning up temporary files... | Hardcoded — GCS cleanup         |
| 100%         | Transcription completed!       | Hardcoded — เสร็จสมบูรณ์           |

> **หมายเหตุ:** ข้อความ Decoding/Recognizing/Generating/Finalizing เป็น **heuristic จาก % range** — Google ให้มาแค่ `progress_percent` (0-100) ไม่ได้บอก stage

**ไฟล์ที่เปลี่ยน:** `gcp_service.py` → `transcribe_audio()`, `task_manager.py` → ทั้งสอง pipeline

---

## สรุป Impact รวม

| Optimization               | เวลาที่ลดได้ (โดยประมาณ)     | ประเภท                |
| -------------------------- | ------------------------- | --------------------- |
| #1 Skip WAV conversion     | 10-30s                    | Performance           |
| #2 Upload compressed       | 5-20x เร็วขึ้น (upload time) | Performance + Cost    |
| #3 Fire-and-forget cleanup | 1-3s                      | Perceived performance |
| #4 Batch tokenization      | 1.5-4s                    | Performance           |
| #5 Skip convert compatible | 5-15s                     | Performance           |
| Granular progress          | —                         | UX improvement        |

**รวมแล้ว:** ลดเวลาต่อคลิปได้ ~20-50 วินาที (ไม่รวมเวลา Google transcribe ซึ่งเป็น fixed cost ที่เราควบคุมไม่ได้)

---

## ไฟล์ที่ถูกแก้ไข

| ไฟล์                                       | การเปลี่ยนแปลง                                                                                                   |
| ----------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `backend/app/services/audio_processor.py` | เพิ่ม `convert_to_opus()`, `is_chirp2_compatible()`, `CHIRP2_SUPPORTED_FORMATS`; เปลี่ยน YouTube download เป็น Opus |
| `backend/app/services/gcp_service.py`     | เพิ่ม `progress_callback` polling, batch `normalize_thai_spaces()`                                               |
| `backend/app/services/task_manager.py`    | Fire-and-forget cleanup, skip convert for compatible files, pass `on_progress` callback                        |
