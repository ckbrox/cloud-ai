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
endpoint = f'https://aiplatform.googleapis.com'
model = 'openai/gpt-oss-120b-maas'



url = f"{endpoint}/v1/projects/{project_id}/locations/{location}/endpoints/openapi/chat/completions"

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {get_access_token()}'
}


data = {
    "model": f"{model}",
    "stream": False,
    "messages": [
        {
            "role": "user",
            "content": "Summer travel plan to Paris"
        }
    ]
}
r = requests.post(url, headers=headers, data=json.dumps(data))
print(r.status_code)
print(r.json())