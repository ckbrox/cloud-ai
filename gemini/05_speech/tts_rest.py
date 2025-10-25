import requests
import requests, json
import google.auth
from google.cloud import resourcemanager_v3
from google.auth.credentials import Credentials
import base64

credentials, project_id = google.auth.default()
credentials.refresh(google.auth.transport.requests.Request())
access_token = credentials.token


url = 'https://texttospeech.googleapis.com/v1/text:synthesize'

headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json',
    'x-goog-user-project': project_id
}

data = {
  "input": {
      "text": "[laughing] oh my god! [sigh] did you see what he is wearing?",
      "prompt": "you are having a casual conversation with a friend and you are amused. say the following:"
  },
  "voice": {
    "languageCode": "en-us",
    "name": "Puck",
    "model_name": "gemini-2.5-pro-tts"
  },
  "audioConfig": {
    "audioEncoding": "LINEAR16"
  }
}

r = requests.post(url, json=data, headers=headers)
print(r.status_code)
audio_content = r.json()['audioContent']
with open('output.mp3', 'wb') as f:
    f.write(base64.b64decode(audio_content))