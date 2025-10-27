import google.auth
from anthropic import AnthropicVertex

_, project_id = google.auth.default()

client = AnthropicVertex(region="global", project_id=project_id)
message = client.messages.create(
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello! Can you help me?"}],
    model="claude-haiku-4-5@20251001"
)
print(message.content[0].text)