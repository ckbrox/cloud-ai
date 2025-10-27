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

location = 'us-central1'
model = 'mistral-medium-3'

endpoint = f'https://{location}-aiplatform.googleapis.com'
if location == 'global':
    endpoint = f'https://aiplatform.googleapis.com'



url = f"{endpoint}/v1/projects/{project_id}/locations/{location}/publishers/mistralai/models/{model}:rawPredict"

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {get_access_token()}'
}

data = {
    "model": f"{model}",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text", "text": "Describe this image in a short sentence."
                    },
                {
                    "type": "image_url", "image_url": {"url": "https://picsum.photos/id/237/200/300"}
                }
            ]
        }
    ]
}

r = requests.post(url, headers=headers, data=json.dumps(data))
print(r.status_code)
print(r.json())