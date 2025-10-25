import requests
import base64
import requests
import google.auth
import google.auth.transport.requests

credentials, project_id = google.auth.default(
      scopes=['https://www.googleapis.com/auth/cloud-platform']
  )

def get_access_token():
    # Get credentials using Application Default Credentials

    # Create a Request object for making HTTP requests
    auth_req = google.auth.transport.requests.Request()

    # Refresh credentials if they are expired
    credentials.refresh(auth_req)

    # Get the access token
    access_token = credentials.token
    return access_token

location = 'us-central1'
model = 'lyria-002'

def generate_music(prompt: str): 
    url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model}:predict"
    data = {
    "instances": [
        {
        "prompt": prompt
        }
    ],
    "parameters": {
        "sample_count": 1 
    }
    }

    r = requests.post(url, json=data, headers={
        'Content-type': 'application/json',
        'Authorization': f'Bearer {get_access_token()}'
    })

    # print(r.json()['predictions'][0].keys())

    try:
        audio_base64_content = r.json()['predictions'][0]['bytesBase64Encoded']
        audio_bytes = base64.b64decode(audio_base64_content)
        return audio_bytes
    except Exception as e:
        print(type(e), e)
        return None



music = generate_music('hip hop edm')
with open('music.wav', 'wb') as f:
    f.write(music)