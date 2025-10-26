from google.cloud.storage import Client, Blob
from uuid import uuid4
import json
import google.auth

_, project_id = google.auth.default()


storage_client = Client()
bucket = storage_client.get_bucket(project_id)


def make_data_from_gcs_directory(directory_name:str, output_file:str='data.jsonl') -> None:

    blobs = storage_client.list_blobs(bucket, prefix=f'{directory_name}/')
    # Print the name of each blob
    with open('data.jsonl', 'w') as f:
        for index, blob in enumerate(list(blobs)):
            blob: Blob
            print(blob.name, blob.content_type)

            display_name = blob.name.split('/')[-1].split('.')[0].replace('_', ' ').title()
            data = {
                "id": str(uuid4()),
                "jsonData": json.dumps({
                    "title": f'Brand Terms: {display_name}',
                    "image_url": "" # public uri
                }),
                "content": {
                    "mimeType": blob.content_type,
                    "uri": f"gs://{project_id}/{blob.name}"
                }
            }

            f.write(json.dumps(data)+'\n')
            f.flush()



