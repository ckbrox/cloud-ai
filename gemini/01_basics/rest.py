import requests
import google.auth
import google.auth.transport.requests
import requests
import json

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

location = 'global'
model = 'gemini-2.5-flash'

endpoint = f'https://{location}-aiplatform.googleapis.com'
if location == 'global':
    endpoint = f'https://aiplatform.googleapis.com'


url = f'{endpoint}/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model}:generateContent'
data = {
  "contents": [{
    "role": "user",
    "parts": [{
      "text": "What's the weather in San Francisco?"
    }]
  }],
  "tools": [{
    "googleSearch": {}
  }],
  "model": f"projects/{project_id}/locations/{location}/publishers/google/models/{model}"
}

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {get_access_token()}'
}


r = requests.post(url, headers=headers, json=data)
print(r.status_code)
print(r.text)