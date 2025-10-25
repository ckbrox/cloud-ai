from google.genai import Client, types
import google.auth

_, project_id = google.auth.default()

client = Client(vertexai=True, project=project_id, location="global")

resposne = client.models.generate_content(
    model='gemini-2.5-flash-image',
    contents=["make a cute puppy"],
    config=types.GenerateContentConfig(
        response_modalities=['IMAGE', 'TEXT']
    )
)

candidate = resposne.candidates[0]
for index, part in enumerate(candidate.content.parts):
    if part.text:
        print(part.text)
    
    if inline_data := part.inline_data:
        with open(f'response_image_{index}.png', 'wb') as f:
            f.write(inline_data.data)
        print(f'response_image_{index}.png')