from google.genai import Client, types
import google.auth

_, project_id = google.auth.default()

client = Client(vertexai=True, project=project_id, location="global")


response = client.models.generate_content(
    model='gemini-flash-lite-latest',
    contents=["What's the weather in San Francisco?"],
    config=types.GenerateContentConfig(
        tools=[
            types.Tool(google_search=types.GoogleSearch())
        ],
    )
)

print(response.model_dump_json(indent=4))