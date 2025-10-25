from google.genai import Client, types
import google.auth
import json 

_, project_id = google.auth.default()

client = Client(vertexai=True, project=project_id, location='us-central1')

response = client.models.generate_content(
    model="model-optimizer-exp-04-09",
    contents="Hey there!",
    config=types.GenerateContentConfig(
        model_selection_config=types.ModelSelectionConfig(
            feature_selection_preference=types.FeatureSelectionPreference.PRIORITIZE_QUALITY  # Options: PRIORITIZE_QUALITY, BALANCED, PRIORITIZE_COST
        ),
    ),
)

print(response.model_dump_json(indent=4))