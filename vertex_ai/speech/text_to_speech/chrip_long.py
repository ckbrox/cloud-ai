from google.cloud import texttospeech
from google.cloud import storage
import google.auth

_, project_id = google.auth.default()

def synthesize_long_audio(text: str, output_gcs_uri: str, voice="en-US-Chirp3-HD-Charon", download:bool=False) -> None:
    """
    Synthesizes long input, writing the resulting audio to `output_gcs_uri`.

    Args:
        project_id: ID or number of the Google Cloud project you want to use.
        output_gcs_uri: Specifies a Cloud Storage URI for the synthesis results.
            Must be specified in the format:
            ``gs://bucket_name/object_name``, and the bucket must
            already exist.
    """

    client = texttospeech.TextToSpeechLongAudioSynthesizeClient()

    input = texttospeech.SynthesisInput(
        text=text,
        markup=text,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", name=voice
    )

    parent = f"projects/{project_id}/locations/us-central1"

    request = texttospeech.SynthesizeLongAudioRequest(
        parent=parent,
        input=input,
        audio_config=audio_config,
        voice=voice,
        output_gcs_uri=output_gcs_uri,
    )

    operation = client.synthesize_long_audio(request=request)
    # Set a deadline for your LRO to finish. 300 seconds is reasonable, but can be adjusted depending on the length of the input.
    # If the operation times out, that likely means there was an error. In that case, inspect the error, and try again.
    result = operation.result(timeout=300)
    print(
        "\nFinished processing, check your GCS bucket to find your audio file! Printing what should be an empty result: ",
        result,
    )