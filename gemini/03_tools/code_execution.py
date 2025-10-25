from google.genai import Client, types
import google.auth

_, project_id = google.auth.default()

client = Client(vertexai=True, project=project_id, location="global")


response = client.models.generate_content(
    model="gemini-flash-latest",
    contents="Calculate 20th fibonacci number. Then find the nearest palindrome to it.",
    config=types.GenerateContentConfig(
        tools=[
            types.Tool(code_execution=types.ToolCodeExecution())
        ],
        temperature=0,
    ),
)
print("# Code:")
print(response.executable_code)
print("# Outcome:")
print(response.code_execution_result)