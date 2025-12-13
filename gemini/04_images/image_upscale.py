from google.auth import default
import google.auth.transport.requests
import base64
import requests

location = "us-central1"

# Programmatically get an access token
credentials, project_id = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
credentials.refresh(google.auth.transport.requests.Request())

with open('source.png', 'rb') as f:
    base64_image = base64.b64encode(f.read()).decode('utf')


url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/imagen-4.0-upscale-preview:predict"

data = {
  "instances": [
    {
      "prompt": "Upscale the image",
      "image": {
        "bytesBase64Encoded": base64_image,
      },
    }
  ],
  "parameters": {
    "mode": "upscale",
    "storageUri": f"gs://{project_id}/images/upscales/",
    "outputOptions": {
      "mimeType": "image/png",
    },
    "upscaleConfig": {
      "upscaleFactor": "x2"
    }
  }
}

r = requests.post(url, json=data, headers={
    'content-type': 'application/json',
    'Authorization': f'Bearer {credentials.token}'
})

print(r.status_code)
print(r.json())