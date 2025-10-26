import requests, json
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


headers = {
    "Authorization": f"Bearer {get_access_token()}",
    "Content-Type": "application/json",
}

data = {
    "instances": [
        {
          "@requestFormat": "chatCompletions",
          "messages": [
              {
                  "role": "user",
                  "content": "What is machine learning? Please, answer in pirate-speak."
              }
          ],
          "max_tokens": 100
        }
    ]
}

ENDPOINT_ID="<your-endpoint-id>"
PROJECT_NUMBER="<your-project-number>"

url = f'https://{ENDPOINT_ID}.europe-west4-{PROJECT_NUMBER}.prediction.vertexai.goog/v1/projects/{PROJECT_NUMBER}/locations/europe-west4/endpoints/{ENDPOINT_ID}:predict'
r = requests.post(url,json=data,headers=headers)
print(json.dumps(r.json(), indent=4))