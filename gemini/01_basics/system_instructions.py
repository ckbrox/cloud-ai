from google.genai import Client, types
import google.auth

_, project_id = google.auth.default()

client = Client(vertexai=True, project=project_id, location="global")

response = client.models.generate_content(
    model="gemini-flash-latest",
    contents="Tell me a story about a robot",
    config=types.GenerateContentConfig(
        system_instruction="You are a pirate."
    )
)

print(response.text)

