from google.genai import Client, types
import google.auth

_, project_id = google.auth.default()

client = Client(vertexai=True, project=project_id, location="global")

response = client.models.generate_content(
    model='gemini-flash-latest',
    contents=['What is this website about: https://ckbrox.com'],
    config=types.GenerateContentConfig(
        tools=[
            types.Tool(url_context=types.UrlContext())
        ]
    )
)

print(response.model_dump_json(indent=4))