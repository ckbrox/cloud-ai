from google.genai import Client, types
import google.auth

_, project_id = google.auth.default()

client = Client(vertexai=True, project=project_id, location="global")

rag_corpus_location = 'us-central1'
rag_corpus_id = '5148740273991319552'

response = client.models.generate_content(
    model="gemini-flash-latest",
    contents="What can you tell me about Early Childhood Education?!",
    config=types.GenerateContentConfig(
        tools=[types.Tool(retrieval=types.Retrieval(vertex_rag_store=types.VertexRagStore(
            rag_resources=[
                types.VertexRagStoreRagResource(
                    rag_corpus=f'projects/{project_id}/locations/{rag_corpus_location}/ragCorpora/{rag_corpus_id}'
                )
            ]
        )))]
    ),
)

print(response.model_dump_json(indent=4))