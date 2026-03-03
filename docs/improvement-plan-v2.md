# แผนปรับปรุงความแม่นยำ VTT — V2 (ฉบับปรับปรุง)

เอกสารนี้เป็นแผนปรับปรุงฉบับที่ 2 ซึ่งแก้ไขข้อผิดพลาดจาก V1 และเพิ่มเติมสิ่งที่ขาดหายไป

---

## สรุปการเปลี่ยนแปลงจาก V1

| หัวข้อ V1 | สถานะ | เหตุผล |
|-----------|--------|--------|
| WAV แทน Opus | ❌ ตัดออก | Opus 64kbps เพียงพอสำหรับ speech, ไฟล์เล็กกว่า 10-15x |
| Audio normalization | ✅ คงไว้ (แก้ไข) | แก้ lowpass จาก 8kHz → 12kHz |
| PyThaiNLP tokenization | ⚠️ ปรับแก้ | แยกชัดว่าช่วยเรื่อง readability ไม่ใช่ accuracy |
| Denoiser config | ✅ คงไว้ | ทำเป็น configurable |
| Custom recognizer | ❌ ตัดออก | Chirp ไม่รองรับ adaptation |
| **VAD (ใหม่)** | ✅ เพิ่ม | ลด hallucination ในช่วงเงียบ |
| **Confidence filtering (ใหม่)** | ✅ เพิ่ม | กรอง segment คุณภาพต่ำ |
| **Audio segmentation (ใหม่)** | ✅ เพิ่ม | เพิ่มความแม่นยำไฟล์ยาว |
| **Post-processing (ใหม่)** | ✅ เพิ่ม | แก้คำซ้ำ, timestamp overlap |

---

## Priority Matrix (ปรับปรุง)

| Priority | หัวข้อ | ผลกระทบต่อความแม่นยำ | ความยาก | ไฟล์ที่แก้ |
|----------|--------|----------------------|---------|-----------|
| **สูง** | Audio normalization (แก้ไข) | สูง | ง่าย | `audio_processor.py` |
| **สูง** | Voice Activity Detection | สูง | ง่าย | `audio_processor.py` |
| **สูง** | Confidence score filtering | สูง | ปานกลาง | `gcp_service.py` |
| **กลาง** | Audio segmentation (ไฟล์ยาว) | ปานกลาง | ปานกลาง | `task_manager.py` |
| **กลาง** | Post-processing (คำซ้ำ/overlap) | ปานกลาง | ปานกลาง | `gcp_service.py` |
| **กลาง** | Denoiser configurable | ปานกลาง | ง่าย | `config.py`, `gcp_service.py` |
| **ต่ำ** | PyThaiNLP readability | ต่ำ (readability) | ปานกลาง | `gcp_service.py` |

---

## 1. Audio Normalization (แก้ไขจาก V1)

### ปัญหาใน V1
- `lowpass=f=8000` ตัดเสียงพยัญชนะภาษาไทย (ส, ช, ศ, ซ) ที่ต้องการความถี่ ~8-12kHz

### แนวทางแก้ไข

```python
# backend/app/services/audio_processor.py

def enhance_audio(input_path: str, task_id: str) -> str:
    """
    Apply audio enhancement for better STT accuracy:
    1. High-pass filter: ลดเสียงความถี่ต่ำ (hum, rumble, AC noise)
    2. Low-pass filter: ลดเสียงความถี่สูงเกินช่วงเสียงพูด
    3. Loudness normalization: ปรับระดับเสียงให้คงที่ตามมาตรฐาน EBU R128
    """
    temp_dir = ensure_temp_dir()
    output_dir = temp_dir / task_id
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "audio_enhanced.opus"

    # Filter chain:
    #   highpass=f=80   → ลด hum/rumble ต่ำกว่า 80Hz
    #   lowpass=f=12000 → ลด hiss สูงกว่า 12kHz (รักษาเสียงพยัญชนะไทย)
    #   loudnorm        → normalize ตาม EBU R128
    #     I=-16   : target integrated loudness
    #     TP=-1.5 : true peak limit
    #     LRA=11  : loudness range
    filter_chain = (
        "highpass=f=80,"
        "lowpass=f=12000,"
        "loudnorm=I=-16:TP=-1.5:LRA=11"
    )

    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-af', filter_chain,
        '-ac', '1',              # Mono
        '-ar', '16000',          # 16kHz
        '-c:a', 'libopus',       # ยังคงใช้ Opus (เล็ก, Chirp 2 รองรับ)
        '-b:a', '64k',
        '-application', 'voip',
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

### การใช้งานใน task_manager.py

```python
# แทนที่ convert_to_opus ด้วย enhance_audio ใน process flow

# ก่อน:
upload_path = await asyncio.to_thread(convert_to_opus, audio_path, task_id)

# หลัง:
from app.services.audio_processor import enhance_audio
upload_path = await asyncio.to_thread(enhance_audio, audio_path, task_id)
```

---

## 2. Voice Activity Detection (VAD) — ใหม่

### ปัญหา
- เมื่อเสียงมีช่วงเงียบยาวๆ (เช่น intro music, ช่วงพัก) STT อาจ **hallucinate** คำที่ไม่มีจริง
- ช่วงเงียบที่มี background noise เบาๆ อาจถูก transcribe เป็นคำไม่มีความหมาย

### แนวทางแก้ไข

```python
# backend/app/services/audio_processor.py

def remove_silence(input_path: str, task_id: str) -> str:
    """
    Remove leading/trailing silence and compress long silent gaps.
    Uses FFmpeg silenceremove filter to clean up audio before STT.

    Parameters:
    - start_periods=1: ลบ silence ที่จุดเริ่มต้น
    - start_silence=0.5: ถ้าเงียบนานกว่า 0.5 วินาทีถือว่า silence
    - start_threshold=-45dB: เสียงที่เบากว่า -45dB ถือว่าเงียบ
    - stop_periods=-1: ลบ silence ทุกช่วงในไฟล์ (ไม่ใช่แค่ต้น/ท้าย)
    - stop_silence=0.8: เก็บ silence ไว้ 0.8 วินาทีเป็น gap ธรรมชาติ
    - stop_threshold=-45dB: threshold เดียวกัน
    """
    temp_dir = ensure_temp_dir()
    output_dir = temp_dir / task_id
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "audio_vad.opus"

    # silenceremove filter:
    # - ลบ silence ที่ต้นไฟล์
    # - บีบอัด silence ตรงกลางให้เหลือ 0.8 วินาที
    # - ลบ silence ที่ท้ายไฟล์
    silence_filter = (
        "silenceremove="
        "start_periods=1:"
        "start_silence=0.5:"
        "start_threshold=-45dB:"
        "stop_periods=-1:"
        "stop_silence=0.8:"
        "stop_threshold=-45dB"
    )

    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-af', silence_filter,
        '-ac', '1',
        '-ar', '16000',
        '-c:a', 'libopus',
        '-b:a', '64k',
        '-application', 'voip',
        '-y',
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        # ถ้า silenceremove ล้มเหลว ใช้ไฟล์เดิม
        print(f"Warning: VAD failed, using original: {result.stderr}")
        return input_path

    original_size = Path(input_path).stat().st_size / (1024 * 1024)
    new_size = output_path.stat().st_size / (1024 * 1024)
    print(f"DEBUG: VAD: {original_size:.1f}MB → {new_size:.1f}MB")

    return str(output_path)
```

### รวม VAD + Enhancement เข้าด้วยกัน

```python
# backend/app/services/audio_processor.py

def prepare_audio_for_stt(input_path: str, task_id: str) -> str:
    """
    Full audio preparation pipeline:
    1. Remove silence (VAD)
    2. Enhance audio (normalize + filter)

    Returns path to the prepared audio file.
    """
    # Step 1: VAD — ลบช่วงเงียบ
    vad_path = remove_silence(input_path, task_id)

    # Step 2: Enhancement — normalize + filter
    enhanced_path = enhance_audio(vad_path, task_id)

    return enhanced_path
```

### การใช้งานใน task_manager.py

```python
# process_youtube_url() — หลัง download

audio_path = await asyncio.to_thread(download_youtube_audio, url, task_id)

# เพิ่ม: เตรียมเสียงก่อน upload
update_task(task_id, TaskStatus.CONVERTING, "Preparing audio...", progress=25)
prepared_path = await asyncio.to_thread(prepare_audio_for_stt, audio_path, task_id)

gcs_uri = await asyncio.to_thread(upload_to_gcs, prepared_path, task_id)
```

---

## 3. Confidence Score Filtering — ใหม่

### ปัญหา
- Google STT V2 ส่ง confidence score กลับมาในแต่ละ segment
- ปัจจุบันโค้ดใช้ VTT output format โดยตรง ซึ่ง **ไม่มี confidence score** ใน VTT
- Segment ที่มี confidence ต่ำมักเป็นคำผิดหรือ hallucination

### แนวทางแก้ไข: ใช้ Inline Results แทน VTT Output

```python
# backend/app/services/gcp_service.py

def transcribe_audio_with_confidence(
    gcs_audio_uri: str,
    task_id: str,
    language_code: Optional[str] = None,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    min_confidence: float = 0.6,
) -> str:
    """
    Transcribe audio with confidence filtering.
    Uses inline results (not VTT output) to access confidence scores,
    then builds VTT manually with only high-confidence segments.

    Args:
        min_confidence: ค่า confidence ขั้นต่ำ (0.0-1.0)
                        segment ที่ต่ำกว่านี้จะถูกตัดออก
    """
    if language_code is None:
        language_code = settings.stt_language_code

    client = get_speech_client()

    parent = f"projects/{settings.google_cloud_project}/locations/{settings.google_cloud_location}"
    recognizer_path = f"{parent}/recognizers/{settings.stt_recognizer}"

    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=[language_code],
        features=cloud_speech.RecognitionFeatures(
            enable_automatic_punctuation=True,
            enable_word_time_offsets=True,
        ),
        denoiser_config=cloud_speech.DenoiserConfig(
            denoise_audio=True,
            snr_threshold=settings.denoise_snr_threshold,
        ),
    )

    if settings.stt_model:
        config.model = settings.stt_model

    # ใช้ inline results แทน VTT output เพื่อเข้าถึง confidence
    output_config = cloud_speech.RecognitionOutputConfig(
        # ไม่ใช้ gcs_output_config — ใช้ inline results
    )

    files = [cloud_speech.BatchRecognizeFileMetadata(uri=gcs_audio_uri)]
    request = cloud_speech.BatchRecognizeRequest(
        recognizer=recognizer_path,
        config=config,
        files=files,
        recognition_output_config=output_config,
    )

    operation = client.batch_recognize(request=request)

    # ... (polling logic เหมือนเดิม) ...

    result = operation.result()

    # สร้าง VTT จาก inline results พร้อม confidence filtering
    vtt_content = _build_vtt_from_results(result, min_confidence)

    # Normalize Thai spaces
    vtt_content = normalize_thai_spaces(vtt_content)

    return vtt_content


def _build_vtt_from_results(
    batch_result,
    min_confidence: float = 0.6,
) -> str:
    """
    Build VTT content from BatchRecognize inline results.
    Filters out segments with confidence below threshold.
    """
    lines = ["WEBVTT", ""]
    segment_num = 0

    for uri, file_result in batch_result.results.items():
        if not hasattr(file_result, 'transcript') or not file_result.transcript:
            continue

        for result in file_result.transcript.results:
            if not result.alternatives:
                continue

            alt = result.alternatives[0]

            # กรอง confidence ต่ำ
            if alt.confidence < min_confidence:
                print(f"DEBUG: Skipped low-confidence segment "
                      f"({alt.confidence:.2f}): {alt.transcript[:50]}")
                continue

            # สร้าง timestamp จาก word_info
            if not alt.words:
                continue

            start_time = alt.words[0].start_offset
            end_time = alt.words[-1].end_offset

            start_str = _format_vtt_time(start_time)
            end_str = _format_vtt_time(end_time)

            segment_num += 1
            lines.append(str(segment_num))
            lines.append(f"{start_str} --> {end_str}")
            lines.append(alt.transcript.strip())
            lines.append("")

    return "\n".join(lines)


def _format_vtt_time(duration) -> str:
    """Convert protobuf Duration to VTT timestamp (HH:MM:SS.mmm)."""
    total_seconds = duration.total_seconds()
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
```

### Configuration

```python
# backend/app/config.py

class Settings(BaseSettings):
    # ... existing settings ...

    # Confidence filtering
    min_confidence: float = 0.6  # 0.0-1.0, segment ต่ำกว่านี้จะถูกตัด
```

```env
# .env
MIN_CONFIDENCE=0.6
```

---

## 4. Audio Segmentation สำหรับไฟล์ยาว — ใหม่

### ปัญหา
- ไฟล์เสียงยาวกว่า 60 นาที ความแม่นยำของ STT ลดลง
- Batch API มี processing time ที่นานขึ้นแบบ non-linear

### แนวทางแก้ไข

```python
# backend/app/services/audio_processor.py

import json

def get_audio_duration(file_path: str) -> float:
    """Get audio duration in seconds using ffprobe."""
    cmd = [
        'ffprobe',
        '-v', 'quiet',
        '-show_entries', 'format=duration',
        '-of', 'json',
        file_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return 0.0

    data = json.loads(result.stdout)
    return float(data.get('format', {}).get('duration', 0))


def split_audio(
    input_path: str,
    task_id: str,
    max_segment_seconds: int = 1800,  # 30 นาที
) -> list[str]:
    """
    Split long audio into segments for better STT accuracy.
    Each segment overlaps by 5 seconds to avoid cutting words.

    Returns list of file paths for each segment.
    """
    duration = get_audio_duration(input_path)

    # ถ้าสั้นกว่า max ไม่ต้องแบ่ง
    if duration <= max_segment_seconds:
        return [input_path]

    temp_dir = ensure_temp_dir()
    output_dir = temp_dir / task_id / "segments"
    output_dir.mkdir(parents=True, exist_ok=True)

    segments = []
    overlap = 5  # วินาที overlap เพื่อไม่ตัดคำ
    start = 0
    seg_num = 0

    while start < duration:
        seg_num += 1
        end = min(start + max_segment_seconds, duration)
        output_path = output_dir / f"segment_{seg_num:03d}.opus"

        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-ss', str(start),
            '-t', str(end - start),
            '-ac', '1',
            '-ar', '16000',
            '-c:a', 'libopus',
            '-b:a', '64k',
            '-application', 'voip',
            '-y',
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            segments.append(str(output_path))
            print(f"DEBUG: Segment {seg_num}: {start:.0f}s - {end:.0f}s")

        # เลื่อน start โดยลบ overlap
        start = end - overlap

    print(f"DEBUG: Split into {len(segments)} segments")
    return segments
```

### การใช้งานใน task_manager.py

```python
# process_youtube_url() — หลัง prepare audio

prepared_path = await asyncio.to_thread(prepare_audio_for_stt, audio_path, task_id)

# ตรวจสอบความยาวและแบ่ง segment ถ้าจำเป็น
segments = await asyncio.to_thread(split_audio, prepared_path, task_id)

if len(segments) == 1:
    # ไฟล์สั้น — process ปกติ
    gcs_uri = await asyncio.to_thread(upload_to_gcs, segments[0], task_id)
    vtt_content = await asyncio.to_thread(transcribe_audio, gcs_uri, task_id, language_code, on_progress)
else:
    # ไฟล์ยาว — process ทีละ segment แล้วรวม
    all_vtt_parts = []
    time_offset = 0.0

    for i, seg_path in enumerate(segments):
        pct = 50 + int((i / len(segments)) * 40)
        update_task(task_id, TaskStatus.TRANSCRIBING,
                    f"Transcribing segment {i+1}/{len(segments)}...", progress=pct)

        gcs_uri = await asyncio.to_thread(upload_to_gcs, seg_path, task_id)
        vtt_part = await asyncio.to_thread(
            transcribe_audio, gcs_uri, task_id, language_code, None
        )
        all_vtt_parts.append((vtt_part, time_offset))

        # คำนวณ offset สำหรับ segment ถัดไป
        _, seg_duration = parse_vtt_metrics(vtt_part)
        time_offset += get_audio_duration(seg_path) - 5  # ลบ overlap

        # Cleanup GCS
        await asyncio.to_thread(delete_from_gcs, gcs_uri)

    vtt_content = merge_vtt_segments(all_vtt_parts)
```

### Merge VTT Segments

```python
# backend/app/services/gcp_service.py

def merge_vtt_segments(segments: list[tuple[str, float]]) -> str:
    """
    Merge multiple VTT segments into one, adjusting timestamps.

    Args:
        segments: list of (vtt_content, time_offset_seconds)
    """
    timestamp_re = re.compile(
        r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})'
    )

    merged_lines = ["WEBVTT", ""]
    segment_num = 0

    for vtt_content, offset in segments:
        for line in vtt_content.split('\n'):
            stripped = line.strip()

            # Skip headers
            if stripped == 'WEBVTT' or not stripped:
                continue

            # Adjust timestamps
            match = timestamp_re.match(stripped)
            if match:
                start = _parse_vtt_time(match.group(1)) + offset
                end = _parse_vtt_time(match.group(2)) + offset
                segment_num += 1
                merged_lines.append(str(segment_num))
                merged_lines.append(
                    f"{_seconds_to_vtt(start)} --> {_seconds_to_vtt(end)}"
                )
            elif stripped.isdigit():
                continue  # Skip old segment numbers
            else:
                merged_lines.append(stripped)
                merged_lines.append("")

    return "\n".join(merged_lines)


def _parse_vtt_time(time_str: str) -> float:
    """Parse VTT timestamp to seconds."""
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)


def _seconds_to_vtt(seconds: float) -> str:
    """Convert seconds to VTT timestamp."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"
```

---

## 5. Post-processing — ใหม่

### ปัญหา
- STT มักสร้างคำซ้ำ (เช่น "ครับ ครับ ครับ")
- Timestamp อาจ overlap กัน
- Segment อาจสั้นเกินไป (< 1 วินาที) หรือยาวเกินไป (> 10 วินาที)

### แนวทางแก้ไข

```python
# backend/app/services/gcp_service.py

def post_process_vtt(vtt_content: str) -> str:
    """
    Post-process VTT content to fix common STT issues:
    1. Remove duplicate consecutive segments
    2. Fix timestamp overlaps
    3. Merge very short segments
    4. Split very long segments
    """
    vtt_content = _remove_duplicate_segments(vtt_content)
    vtt_content = _fix_timestamp_overlaps(vtt_content)
    vtt_content = _merge_short_segments(vtt_content, min_duration=1.0)
    return vtt_content


def _remove_duplicate_segments(vtt_content: str) -> str:
    """
    Remove consecutive segments with identical or near-identical text.
    Common STT artifact: "ครับ" repeated 3 times in a row.
    """
    lines = vtt_content.split('\n')
    timestamp_re = re.compile(
        r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})'
    )

    # Parse into segments
    segments = []
    current_segment = {}

    for line in lines:
        stripped = line.strip()
        if stripped == 'WEBVTT':
            continue
        if not stripped:
            if current_segment.get('text'):
                segments.append(current_segment)
                current_segment = {}
            continue

        match = timestamp_re.match(stripped)
        if match:
            current_segment['start'] = match.group(1)
            current_segment['end'] = match.group(2)
        elif stripped.isdigit():
            current_segment['num'] = stripped
        else:
            current_segment['text'] = current_segment.get('text', '') + stripped

    if current_segment.get('text'):
        segments.append(current_segment)

    # Remove duplicates
    filtered = []
    prev_text = None
    for seg in segments:
        text = seg.get('text', '').strip()
        if text == prev_text:
            print(f"DEBUG: Removed duplicate segment: {text[:50]}")
            continue
        filtered.append(seg)
        prev_text = text

    # Rebuild VTT
    result_lines = ["WEBVTT", ""]
    for i, seg in enumerate(filtered, 1):
        result_lines.append(str(i))
        result_lines.append(f"{seg['start']} --> {seg['end']}")
        result_lines.append(seg.get('text', ''))
        result_lines.append("")

    return "\n".join(result_lines)


def _fix_timestamp_overlaps(vtt_content: str) -> str:
    """
    Fix overlapping timestamps by adjusting end time of previous segment
    to match start time of next segment.
    """
    lines = vtt_content.split('\n')
    timestamp_re = re.compile(
        r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})'
    )

    timestamps = []
    timestamp_indices = []

    for i, line in enumerate(lines):
        match = timestamp_re.match(line.strip())
        if match:
            start = _parse_vtt_time(match.group(1))
            end = _parse_vtt_time(match.group(2))
            timestamps.append((start, end))
            timestamp_indices.append(i)

    # Fix overlaps
    for j in range(len(timestamps) - 1):
        current_end = timestamps[j][1]
        next_start = timestamps[j + 1][0]

        if current_end > next_start:
            # ปรับ end time ของ segment ปัจจุบันให้ตรงกับ start ของ segment ถัดไป
            fixed_end = next_start - 0.001  # ลบ 1ms
            if fixed_end > timestamps[j][0]:  # ต้องมากกว่า start
                timestamps[j] = (timestamps[j][0], fixed_end)
                lines[timestamp_indices[j]] = (
                    f"{_seconds_to_vtt(timestamps[j][0])} --> "
                    f"{_seconds_to_vtt(fixed_end)}"
                )
                print(f"DEBUG: Fixed overlap at segment {j+1}")

    return "\n".join(lines)


def _merge_short_segments(vtt_content: str, min_duration: float = 1.0) -> str:
    """
    Merge segments shorter than min_duration with adjacent segments.
    Very short segments often contain incomplete words or noise.
    """
    # Parse segments
    lines = vtt_content.split('\n')
    timestamp_re = re.compile(
        r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})'
    )

    segments = []
    current = {}

    for line in lines:
        stripped = line.strip()
        if stripped == 'WEBVTT':
            continue
        if not stripped:
            if current.get('text'):
                segments.append(current)
                current = {}
            continue

        match = timestamp_re.match(stripped)
        if match:
            current['start_s'] = _parse_vtt_time(match.group(1))
            current['end_s'] = _parse_vtt_time(match.group(2))
        elif stripped.isdigit():
            pass
        else:
            current['text'] = current.get('text', '') + ' ' + stripped

    if current.get('text'):
        segments.append(current)

    # Merge short segments with next segment
    merged = []
    i = 0
    while i < len(segments):
        seg = segments[i]
        duration = seg['end_s'] - seg['start_s']

        if duration < min_duration and i + 1 < len(segments):
            # Merge with next segment
            next_seg = segments[i + 1]
            merged_seg = {
                'start_s': seg['start_s'],
                'end_s': next_seg['end_s'],
                'text': (seg.get('text', '') + ' ' + next_seg.get('text', '')).strip()
            }
            merged.append(merged_seg)
            i += 2  # Skip next
            print(f"DEBUG: Merged short segment ({duration:.2f}s)")
        else:
            merged.append(seg)
            i += 1

    # Rebuild VTT
    result_lines = ["WEBVTT", ""]
    for j, seg in enumerate(merged, 1):
        result_lines.append(str(j))
        result_lines.append(
            f"{_seconds_to_vtt(seg['start_s'])} --> {_seconds_to_vtt(seg['end_s'])}"
        )
        result_lines.append(seg.get('text', '').strip())
        result_lines.append("")

    return "\n".join(result_lines)
```

---

## 6. Denoiser Configurable (จาก V1)

```python
# backend/app/config.py

class Settings(BaseSettings):
    # ... existing settings ...

    # Denoiser
    denoise_snr_threshold: float = 20.0

    # Confidence filtering
    min_confidence: float = 0.6

    # Audio segmentation
    max_segment_seconds: int = 1800  # 30 นาที
```

```python
# backend/app/services/gcp_service.py — ใน transcribe_audio()

"denoiser_config": cloud_speech.DenoiserConfig(
    denoise_audio=True,
    snr_threshold=settings.denoise_snr_threshold,  # ใช้จาก config
),
```

```env
# .env
DENOISE_SNR_THRESHOLD=20.0
MIN_CONFIDENCE=0.6
MAX_SEGMENT_SECONDS=1800
```

---

## สรุป Pipeline ใหม่

```
User Input (YouTube URL / Audio File)
         │
         ▼
┌─ Step 1: Acquire Audio ──────────────────────┐
│  YouTube: yt-dlp → Opus                      │
│  Upload: save to /tmp/                       │
└──────────────┬───────────────────────────────┘
               ▼
┌─ Step 2: Voice Activity Detection (ใหม่) ────┐
│  FFmpeg silenceremove filter                  │
│  ลบช่วงเงียบ, ลด hallucination               │
└──────────────┬───────────────────────────────┘
               ▼
┌─ Step 3: Audio Enhancement (ปรับปรุง) ───────┐
│  highpass=80Hz, lowpass=12kHz (แก้จาก 8kHz)  │
│  loudnorm (EBU R128)                          │
└──────────────┬───────────────────────────────┘
               ▼
┌─ Step 4: Audio Segmentation (ใหม่) ──────────┐
│  ถ้า > 30 นาที → แบ่งเป็น segments           │
│  overlap 5 วินาที                             │
└──────────────┬───────────────────────────────┘
               ▼
┌─ Step 5: Upload to GCS ─────────────────────┐
│  gs://bucket/audio/<task_id>/                │
└──────────────┬───────────────────────────────┘
               ▼
┌─ Step 6: Google STT V2 Batch API ────────────┐
│  Chirp 2 + Denoiser (configurable SNR)       │
│  Confidence score filtering (ใหม่)            │
└──────────────┬───────────────────────────────┘
               ▼
┌─ Step 7: Post-processing (ใหม่) ────────────┐
│  ลบ segment ซ้ำ                               │
│  แก้ timestamp overlap                        │
│  รวม segment สั้นเกินไป                       │
└──────────────┬───────────────────────────────┘
               ▼
┌─ Step 8: Thai Text Normalization ────────────┐
│  PyThaiNLP normalize_thai_spaces()           │
└──────────────┬───────────────────────────────┘
               ▼
         Download VTT
```

---

## แผนการ Implement

### Phase 1: Quick Wins (1-2 ชั่วโมง)
- [ ] เพิ่ม `enhance_audio()` ใน `audio_processor.py` (แก้ lowpass เป็น 12kHz)
- [ ] เพิ่ม `remove_silence()` (VAD) ใน `audio_processor.py`
- [ ] ทำ `denoise_snr_threshold` เป็น configurable ใน `config.py`

### Phase 2: Core Improvements (3-4 ชั่วโมง)
- [ ] เพิ่ม `post_process_vtt()` ใน `gcp_service.py`
- [ ] เพิ่ม `_remove_duplicate_segments()`
- [ ] เพิ่ม `_fix_timestamp_overlaps()`
- [ ] เพิ่ม `_merge_short_segments()`
- [ ] อัพเดท `task_manager.py` ให้ใช้ pipeline ใหม่

### Phase 3: Advanced (1 วัน)
- [ ] Implement confidence score filtering (ต้องเปลี่ยนจาก VTT output เป็น inline results)
- [ ] Implement audio segmentation สำหรับไฟล์ยาว
- [ ] Implement `merge_vtt_segments()`
- [ ] ทดสอบกับ dataset หลายๆ แบบ

---

## References

- [Google Cloud Speech-to-Text V2 — Batch Recognize](https://cloud.google.com/speech-to-text/v2/docs/batch-recognize)
- [Google Cloud Speech-to-Text V2 — Chirp 2](https://cloud.google.com/speech-to-text/v2/docs/chirp-model)
- [FFmpeg silenceremove filter](https://ffmpeg.org/ffmpeg-filters.html#silenceremove)
- [FFmpeg loudnorm filter](https://ffmpeg.org/ffmpeg-filters.html#loudnorm)
- [EBU R128 Loudness Standard](https://tech.ebu.ch/docs/r/r128.pdf)
- [PyThaiNLP Tokenization](https://pythainlp.github.io/docs/5.0/api/tokenize.html)
