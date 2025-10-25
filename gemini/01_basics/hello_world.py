from google.genai import Client, types
import google.auth

_, project_id = google.auth.default()

client = Client(vertexai=True, project=project_id, location="global")

response = client.models.generate_content(
    model="gemini-flash-latest",
    contents="Hello Gemini",
)

print(response.text)

