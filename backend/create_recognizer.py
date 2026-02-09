from google.cloud import speech_v2
from google.api_core.client_options import ClientOptions
import os

def create_chirp_recognizer(project_id, location, recognizer_id):
    client_options = ClientOptions(api_endpoint=f"{location}-speech.googleapis.com")
    client = speech_v2.SpeechClient(client_options=client_options)

    parent = f"projects/{project_id}/locations/{location}"
    
    print(f"Creating recognizer '{recognizer_id}' in {parent}...")

    recognizer = speech_v2.Recognizer(
        model="chirp",
        language_codes=["th-TH"], # Chirp model supports single language in this region
        default_recognition_config=speech_v2.RecognitionConfig(
            features=speech_v2.RecognitionFeatures(
                enable_automatic_punctuation=True,
                enable_word_time_offsets=True,
            )
        )
    )

    request = speech_v2.CreateRecognizerRequest(
        parent=parent,
        recognizer=recognizer,
        recognizer_id=recognizer_id
    )

    try:
        operation = client.create_recognizer(request=request)
        result = operation.result(timeout=120)
        print(f"Successfully created recognizer: {result.name}")
    except Exception as e:
        print(f"Error creating recognizer: {e}")

if __name__ == "__main__":
    # Load credentials from environment or hardcode for this script
    # backend/.env has GOOGLE_CLOUD_PROJECT=autovtt-engine
    create_chirp_recognizer("autovtt-engine", "asia-southeast1", "chirp-thai-recognizer")
