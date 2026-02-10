from google.genai import Client, types
import google.auth
from uuid import uuid4

_, project_id = google.auth.default()

client = Client(vertexai=True, project=project_id, location="global")

response = client.models.generate_content(
    model='gemini-3-pro-image-preview',
    contents=["make 3 images of a cute puppy jumping over a wall"],
    config=types.GenerateContentConfig(
        response_modalities=['IMAGE', 'TEXT']
    )
)




candidate = response.candidates[0]
generation_id = uuid4().hex
for index, part in enumerate(candidate.content.parts):
    if part.text:
        print(part.text)
    
    if inline_data := part.inline_data:
        with open(f'temp/response_image_{generation_id}-{index}.png', 'wb') as f:
            f.write(inline_data.data)
        print(f'response_image_{index}.png')


print(response.usage_metadata.model_dump_json(indent=4))