import requests
import json
import google.auth
import google.auth.transport.requests

credentials, project_id = google.auth.default(
    scopes=['https://www.googleapis.com/auth/cloud-platform']
)

def get_access_token():
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    return credentials.token

headers = {
    "Authorization": f"Bearer {get_access_token()}",
    "Content-Type": "application/json",
}

url = f"https://aiplatform.googleapis.com/v1/projects/{project_id}/locations/global/endpoints/openapi/chat/completions"

data = {
    "model": "google/gemma-4-26b-a4b-it-maas",
    "stream": False,
    "messages": [{"role": "user", "content": "Summer travel plan to Paris"}]
}

response = requests.post(url, headers=headers, json=data)

print(f"Status Code: {response.status_code}")
try:
    print(json.dumps(response.json(), indent=2))
except json.JSONDecodeError:
    print(response.text)
