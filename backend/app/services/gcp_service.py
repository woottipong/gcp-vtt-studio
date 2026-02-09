from google.cloud import storage
from google.cloud import speech_v2 as speech
from google.cloud.speech_v2 import types as cloud_speech
from google.api_core.client_options import ClientOptions
from pathlib import Path
import re
import time
from typing import Optional, Callable
from pythainlp.tokenize import word_tokenize
from app.config import get_settings

settings = get_settings()


# Singleton pattern for GCS Storage Client
_storage_client: Optional[storage.Client] = None


def get_storage_client() -> storage.Client:
    """Get or create singleton GCS storage client."""
    global _storage_client
    if _storage_client is None:
        if settings.google_application_credentials:
            _storage_client = storage.Client.from_service_account_json(
                settings.google_application_credentials,
                project=settings.google_cloud_project
            )
        else:
            _storage_client = storage.Client(project=settings.google_cloud_project)
    return _storage_client


# Singleton pattern for Speech Client
_speech_client: Optional[speech.SpeechClient] = None


def get_speech_client() -> speech.SpeechClient:
    """Get or create singleton Speech-to-Text client."""
    global _speech_client
    if _speech_client is None:
        client_options = None
        if settings.google_cloud_location != "global":
            api_endpoint = f"{settings.google_cloud_location}-speech.googleapis.com"
            client_options = ClientOptions(api_endpoint=api_endpoint)
        
        if settings.google_application_credentials:
            _speech_client = speech.SpeechClient.from_service_account_json(
                settings.google_application_credentials,
                client_options=client_options
            )
        else:
            _speech_client = speech.SpeechClient(client_options=client_options)
    return _speech_client


def upload_to_gcs(local_file_path: str, task_id: str) -> str:
    """
    Upload a file to Google Cloud Storage.
    Returns the GCS URI (gs://bucket/path).
    """
    client = get_storage_client()
    bucket = client.bucket(settings.google_cloud_storage_bucket)
    
    file_name = Path(local_file_path).name
    blob_name = f"audio/{task_id}/{file_name}"
    blob = bucket.blob(blob_name)
    
    blob.upload_from_filename(local_file_path)
    
    return f"gs://{settings.google_cloud_storage_bucket}/{blob_name}"


def delete_from_gcs(gcs_uri: str) -> None:
    """Delete a file from Google Cloud Storage."""
    if not gcs_uri.startswith("gs://"):
        return
    
    path = gcs_uri.replace("gs://", "")
    bucket_name = path.split("/")[0]
    blob_name = "/".join(path.split("/")[1:])
    
    client = get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    if blob.exists():
        blob.delete()


def transcribe_audio(
    gcs_audio_uri: str,
    task_id: str,
    language_code: Optional[str] = None,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> str:
    """
    Transcribe audio using Google Cloud Speech-to-Text V2 Batch API.
    Google generates VTT directly and writes to GCS temporarily.
    We download the VTT content, then delete the GCS VTT files.
    
    Args:
        progress_callback: Optional callback(progress_percent, message) to report
                          granular progress during transcription.
    Returns VTT content as a string.
    """
    # Use language code from settings if not provided
    if language_code is None:
        language_code = settings.stt_language_code
    
    client = get_speech_client()

    # Configure the temporary output location for VTT on GCS
    output_bucket = settings.google_cloud_storage_bucket
    output_prefix = f"vtt/{task_id}/"
    gcs_output_uri = f"gs://{output_bucket}/{output_prefix}"

    # Build the recognizer name
    parent = f"projects/{settings.google_cloud_project}/locations/{settings.google_cloud_location}"
    recognizer_path = f"{parent}/recognizers/{settings.stt_recognizer}"

    # Configure recognition settings (following Chirp 2 best practices)
    config_params = {
        "auto_decoding_config": cloud_speech.AutoDetectDecodingConfig(),
        "language_codes": [language_code],
        "features": cloud_speech.RecognitionFeatures(
            enable_automatic_punctuation=True,
            enable_word_time_offsets=True,  # Required for VTT output format
        ),
        # Enable denoiser to reduce background music/noise (Chirp 2 feature)
        "denoiser_config": cloud_speech.DenoiserConfig(
            denoise_audio=True,
            snr_threshold=20.0,  # Medium sensitivity (recommended for general use)
        ),
    }
    
    # Only override model if explicitly set (otherwise use recognizer's default)
    if settings.stt_model:
        config_params["model"] = settings.stt_model
    
    config = cloud_speech.RecognitionConfig(**config_params)

    # Use GCS output with VTT format (Google handles segmentation)
    output_config = cloud_speech.RecognitionOutputConfig(
        gcs_output_config=cloud_speech.GcsOutputConfig(
            uri=gcs_output_uri,
        ),
        output_format_config=cloud_speech.OutputFormatConfig(
            vtt=cloud_speech.VttOutputFileFormatConfig(),
        ),
    )

    # Create batch recognition request
    files = [cloud_speech.BatchRecognizeFileMetadata(uri=gcs_audio_uri)]
    request = cloud_speech.BatchRecognizeRequest(
        recognizer=recognizer_path,
        config=config,
        files=files,
        recognition_output_config=output_config,
    )

    # Execute the batch recognition
    operation = client.batch_recognize(request=request)
    print(f"Waiting for transcription to complete (task_id: {task_id})...")

    if progress_callback:
        progress_callback(60, "Queued for transcription...")

    # Poll operation for granular progress instead of blocking on result()
    try:
        deadline = time.time() + settings.transcription_timeout
        last_pct = -1
        
        while not operation.done():
            if time.time() > deadline:
                try:
                    operation.cancel()
                except Exception:
                    pass
                raise TimeoutError(f"Transcription timed out after {settings.transcription_timeout}s")
            
            # Extract progress from operation metadata
            if progress_callback:
                try:
                    metadata = operation.metadata
                    if metadata and hasattr(metadata, 'transcription_metadata'):
                        for _uri, file_meta in metadata.transcription_metadata.items():
                            pct = getattr(file_meta, 'progress_percent', 0)
                            if pct != last_pct:
                                last_pct = pct
                                # Map Google's 0-100% to our 60-90% range
                                mapped = 60 + int(pct * 0.3)
                                if pct < 20:
                                    msg = "Decoding audio..."
                                elif pct < 50:
                                    msg = f"Recognizing speech... ({pct}%)"
                                elif pct < 80:
                                    msg = f"Generating subtitles... ({pct}%)"
                                else:
                                    msg = f"Finalizing results... ({pct}%)"
                                progress_callback(mapped, msg)
                except Exception:
                    pass  # Metadata parsing is best-effort
            
            time.sleep(3)  # Poll every 3 seconds
        
        result = operation.result()
        
    except TimeoutError:
        raise
    except Exception as e:
        try:
            operation.cancel()
        except Exception:
            pass
        raise TimeoutError(f"Transcription failed: {str(e)}")

    if progress_callback:
        progress_callback(90, "Downloading subtitles...")

    # Get the VTT file URI from results
    vtt_gcs_uri = None
    if result and hasattr(result, 'results') and result.results:
        for uri, file_result in result.results.items():
            if hasattr(file_result, 'cloud_storage_result') and file_result.cloud_storage_result:
                vtt_uri = file_result.cloud_storage_result.vtt_format_uri
                if vtt_uri:
                    vtt_gcs_uri = vtt_uri
                    break

    if not vtt_gcs_uri:
        raise RuntimeError("No VTT file generated by Google STT")

    # Download VTT content from GCS
    vtt_content = _download_text_from_gcs(vtt_gcs_uri)

    if progress_callback:
        progress_callback(93, "Normalizing Thai text...")

    vtt_content = normalize_thai_spaces(vtt_content)

    if progress_callback:
        progress_callback(96, "Cleaning up temporary files...")

    # Cleanup: delete temporary VTT files from GCS
    _delete_gcs_prefix(output_bucket, output_prefix)

    return vtt_content


def _download_text_from_gcs(gcs_uri: str) -> str:
    """Download text content from a GCS URI."""
    if not gcs_uri.startswith("gs://"):
        raise ValueError("Invalid GCS URI")
    path = gcs_uri.replace("gs://", "")
    bucket_name = path.split("/")[0]
    blob_name = "/".join(path.split("/")[1:])

    client = get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.download_as_text()


def _delete_gcs_prefix(bucket_name: str, prefix: str) -> None:
    """Delete all objects under a GCS prefix."""
    try:
        client = get_storage_client()
        bucket = client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=prefix)
        for blob in blobs:
            blob.delete()
        print(f"Cleaned up GCS: gs://{bucket_name}/{prefix}")
    except Exception as e:
        print(f"Warning: Failed to cleanup GCS prefix {prefix}: {e}")


# Thai particles that end a clause/sentence — add space AFTER these
_CLAUSE_END_PARTICLES = {
    'ครับ', 'ค่ะ', 'คะ', 'จ้ะ', 'จ้า', 'จ๊ะ', 'นะ', 'นะครับ', 'นะคะ',
    'นะค่ะ', 'ค่า', 'คับ', 'ฮะ', 'ฮ่ะ', 'เลย', 'ด้วย',
}

# Thai conjunctions/clause starters — add space BEFORE these
_CLAUSE_STARTERS = {
    'แต่', 'แต่ว่า', 'เพราะ', 'เพราะว่า', 'ถ้า', 'ถ้าเกิด',
    'ดังนั้น', 'ซึ่ง', 'หรือว่า', 'แล้วก็',
    'อย่างไรก็ตาม', 'นอกจากนี้', 'รวมถึง', 'สําหรับ',
}


def normalize_thai_spaces(vtt_text: str) -> str:
    """
    Normalize Thai spacing in VTT content.
    Google STT Chirp model adds spaces between every Thai word token.
    This function:
      1. Collects all subtitle text lines
      2. Batch-joins Thai text, removes extra spaces, then tokenizes ONCE
      3. Re-adds spaces at natural clause/phrase boundaries
    Only processes the text portion of VTT cues, not timestamps or headers.
    """
    lines = vtt_text.split('\n')
    timestamp_re = re.compile(r'^\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}')

    # First pass: collect Thai text lines and their indices
    text_indices = []
    thai_segments_raw = []

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if (
            not stripped
            or stripped == 'WEBVTT'
            or stripped.isdigit()
            or timestamp_re.match(stripped)
        ):
            continue
        text_indices.append(idx)
        thai_segments_raw.append(stripped)

    if not thai_segments_raw:
        return vtt_text

    # Second pass: extract Thai-only text from all lines, batch tokenize once
    all_thai_parts = []
    line_thai_ranges = []  # (start, end) indices into all_thai_parts per line

    for raw_line in thai_segments_raw:
        segments = re.split(r'((?:[a-zA-Z0-9]+(?:\s+[a-zA-Z0-9]*)*))', raw_line)
        start = len(all_thai_parts)
        for segment in segments:
            if not segment:
                continue
            if not re.match(r'^[a-zA-Z0-9]', segment.strip()):
                thai_text = re.sub(r'\s+', '', segment)
                if thai_text:
                    all_thai_parts.append(thai_text)
        line_thai_ranges.append((start, len(all_thai_parts)))

    # Batch tokenize: join all Thai parts with a unique separator, tokenize once
    _SEP = '\u200b'  # Zero-width space as separator
    joined = _SEP.join(all_thai_parts)
    all_tokens = word_tokenize(joined, engine='newmm') if joined else []

    # Split tokens back by separator
    tokenized_parts = []
    current = []
    for token in all_tokens:
        if token == _SEP:
            tokenized_parts.append(current)
            current = []
        else:
            current.append(token)
    tokenized_parts.append(current)

    # Third pass: rebuild each line with clause spacing
    part_idx = 0
    for line_idx, raw_line in zip(text_indices, thai_segments_raw):
        segments = re.split(r'((?:[a-zA-Z0-9]+(?:\s+[a-zA-Z0-9]*)*))', raw_line)
        processed = []
        for segment in segments:
            if not segment:
                continue
            if re.match(r'^[a-zA-Z0-9]', segment.strip()):
                processed.append(f' {segment.strip()} ')
            else:
                thai_text = re.sub(r'\s+', '', segment)
                if thai_text and part_idx < len(tokenized_parts):
                    processed.append(_add_clause_spaces_from_tokens(tokenized_parts[part_idx]))
                    part_idx += 1
        result = ''.join(processed).strip()
        result = re.sub(r'\s{2,}', ' ', result)
        lines[line_idx] = result

    return '\n'.join(lines)


def _add_clause_spaces_from_tokens(words: list) -> str:
    """
    Insert spaces at clause/phrase boundaries from pre-tokenized words.
    """
    if not words:
        return ''

    result_parts = []
    i = 0
    while i < len(words):
        word = words[i]

        if word.strip() == '':
            i += 1
            continue

        # Check for multi-word clause starters
        if i + 1 < len(words):
            two_word = word + words[i + 1]
            if two_word in _CLAUSE_STARTERS and result_parts:
                result_parts.append(' ')
                result_parts.append(two_word)
                i += 2
                continue

        if word in _CLAUSE_STARTERS and result_parts:
            result_parts.append(' ')
            result_parts.append(word)
            i += 1
            continue

        if word in _CLAUSE_END_PARTICLES and i + 1 < len(words):
            result_parts.append(word)
            result_parts.append(' ')
            i += 1
            continue

        result_parts.append(word)
        i += 1

    return ''.join(result_parts)
