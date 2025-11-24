from google.genai import Client, types
import google.auth
from uuid import uuid4

_, project_id = google.auth.default()

client = Client(vertexai=True, project=project_id, location="global")

message = 'GET WELL'

with open('source.png', 'rb') as f:
    image_part = types.Part.from_bytes(data=f.read(), mime_type='image/png')



for letter in message:
    if letter == ' ':
        continue
    
    resposne = client.models.generate_content(
        model='gemini-3-pro-image-preview',
        contents=[image_part, f'Make the man contort his body in the shape of the letter {letter} on a flat white background. His shape should be clearly the letter {letter} with no extras'],
        config=types.GenerateContentConfig(
            response_modalities=['IMAGE']
        )
    )

    candidate = resposne.candidates[0] 
    for index, part in enumerate(candidate.content.parts):
        if part.text:
            print(part.text)
        
        if inline_data := part.inline_data:
            image_name = f'{letter}-{uuid4().hex}.png'
            with open(image_name, 'wb') as f:
                f.write(inline_data.data)


