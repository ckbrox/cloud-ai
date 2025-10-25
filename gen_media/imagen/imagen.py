from google.genai import Client, types
import google.auth

_, project_id = google.auth.default()

client = Client(vertexai=True, project=project_id, location="global")

res = client.models.generate_images(
    model='imagen-4.0-ultra-generate-001',
    prompt='A dog',
    config=types.GenerateImagesConfig(
        number_of_images=1
    )
)

image = res.generated_images[0].image.image_bytes
with open('dog.png', 'wb') as f:
    f.write(image)