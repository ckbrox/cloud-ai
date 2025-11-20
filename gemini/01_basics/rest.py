import requests
import google.auth
import google.auth.transport.requests
import requests
import json

credentials, project_id = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
credentials.refresh(google.auth.transport.requests.Request())

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
    'Authorization': f'Bearer {credentials.token}'
}


r = requests.post(url, headers=headers, json=data)
print(r.status_code)
print(r.text)