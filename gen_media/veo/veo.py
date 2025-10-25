# from google_cloud import google_cloud_client
from google.genai import types, Client
from time import sleep
import google.auth

_, project_id = google.auth.default()

client = Client(vertexai=True, project=project_id, location="global")


operation = client.models.generate_videos(
    model='veo-3.1-generate-preview',
    prompt='a puppy eating vegan ice cream',
    config=types.GenerateVideosConfig(
        number_of_videos=1,
        output_gcs_uri=f'gs://{project_id}/veo/', # replace with your Google Cloud Storage bucket
    )
)

while not operation.done:
    print(f'Operation not done... sleeping for 10 seconds')
    sleep(10)
    operation = client.operations.get(operation)
    print(operation)


video_uri = operation.result.generated_videos[0].video.uri
authenticated_uri = f'https://storage.cloud.google.com/{video_uri.replace("gs://", "")}'

print(f'Finished. You can view the video at: {authenticated_uri}\n Make sure to access this url in a browser that is logged into your Google Cloud account.')