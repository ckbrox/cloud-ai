

from google.genai import Client, types
import google.auth

import json

_, project_id = google.auth.default()
client = Client(vertexai=True, project=project_id, location="global")

response = client.models.generate_content(
    model="gemini-flash-latest",
    contents="I love San Francisco so much, it's awesome",
    config=types.GenerateContentConfig(
        response_logprobs=True,
        logprobs=3,
        system_instruction="You are a sentiment classifier. Your response should be one word (positive, negative, or neutral)",
    )
)

print(response.model_dump_json(indent=4))

