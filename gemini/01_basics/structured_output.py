from google.genai import Client, types
import json
import google.auth

_, project_id = google.auth.default()

client = Client(vertexai=True, project=project_id, location='global')

response = client.models.generate_content(
    model='gemini-flash-latest',
    contents=['Create recipe for vegan, cacao cookies'],
    config=types.GenerateContentConfig(
        response_mime_type='application/json',
        response_schema={
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'ingredients': {
                    'type': 'array', 
                    'items': {
                        'type': 'string',
                    },
                    'minItems': 5
                },
                'instructions': {'type': 'array', 'items': {'type': 'string'}},
                'details': {
                    'type': 'object',
                    'properties': {
                        'prep_time_minutes': {'type': 'number'},
                        'cook_time_minutes': {'type': 'number'},
                        'servings': {'type': 'number'}
                    },
                    'required': ['prep_time_minutes', 'cook_time_minutes', 'servings']
                }
            },
            'required': ['name', 'ingredients', 'instructions']
        }
    )
)

data = json.loads(response.text)
print(json.dumps(data,indent=4))