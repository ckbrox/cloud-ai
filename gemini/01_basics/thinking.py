from google.genai import Client, types
import google.auth

_, project_id = google.auth.default()

client = Client(vertexai=True, project=project_id, location="global")


response = client.models.generate_content(
    model='gemini-flash-latest',
    contents=['What are the pros and cons of a Central Bank? How has the US central bank evolved since its inception?'],
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=10000
        )    
    )
)

print(response.model_dump_json(indent=4))