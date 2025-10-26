from google.genai import Client, types
import google.auth

_, project_id = google.auth.default()

client = Client(vertexai=True, project=project_id, location="global")

'''
CREATE A CACHE
'''

video = types.Part.from_uri(
    file_uri=f'gs://{project_id}/veo/10555521992336190248/sample_0.mp4',
    mime_type='video/mp4'
)

cache = client.caches.create(
    model='gemini-flash-latest',
    config=types.CreateCachedContentConfig(
        contents=[
            video, 
            'summarize the video'
        ],
        display_name='testCacheVeoVid',
    )
)

print(cache.model_dump_json(indent=4))


'''
USE A CACHE
'''

cache_name = cache.name

# cache_name = 'projects/<your-project-number>/locations/global/cachedContents/<cache-id>'


response = client.models.generate_content(
    model='gemini-flash-latest',
    contents='what color is the puppy?',
    config=types.GenerateContentConfig(
        cached_content=cache_name
    )
)

print(response.model_dump_json(indent=4))