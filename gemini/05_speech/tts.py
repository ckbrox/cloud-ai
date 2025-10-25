import os
from google.cloud import texttospeech

def synthesize(prompt: str, text: str, model_name: str, output_filepath: str = "output.mp3"):
   """Synthesizes speech from the input text and saves it to an MP3 file.

   Args:
       prompt: Stylisting instructions on how to synthesize the content in
         the text field.
       text: The text to synthesize.
       model_name: Gemini model to use. Currently, the available models are
         gemini-2.5-flash-preview-tts and gemini-2.5-pro-preview-tts
       output_filepath: The path to save the generated audio file.
         Defaults to "output.mp3".
   """
   client = texttospeech.TextToSpeechClient()

   synthesis_input = texttospeech.SynthesisInput(text=text, prompt=prompt)

   # Select the voice you want to use.
   voice = texttospeech.VoiceSelectionParams(
       language_code="en-US",
       name="Charon",  # Example voice, adjust as needed
       model_name=model_name
   )

   audio_config = texttospeech.AudioConfig(
       audio_encoding=texttospeech.AudioEncoding.MP3
   )

   # Perform the text-to-speech request on the text input with the selected
   # voice parameters and audio file type.
   response = client.synthesize_speech(
       input=synthesis_input, voice=voice, audio_config=audio_config
   )

   # The response's audio_content is binary.
   with open(output_filepath, "wb") as out:
       out.write(response.audio_content)
       print(f"Audio content written to file: {output_filepath}")


text = "Hey there, I'm Gemini your friendly personal assistant. How can I help you today?"
prompt ="A quiet whisper"
model_name = "gemini-2.5-pro-tts"
output_filepath = "output.mp3"

synthesize(prompt, text, model_name, output_filepath)