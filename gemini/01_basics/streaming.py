from google.genai import Client, types
import google.auth

_, project_id = google.auth.default()

client = Client(vertexai=True, project=project_id, location='global')

streamer = client.models.generate_content_stream(
    model='gemini-flash-lite-latest',
    contents="Tell me a story about a robot"
)

for chunk in streamer:
    print(chunk.text, end="")