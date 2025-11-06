from google.genai import Client, types
import google.auth
import json

_, project_id = google.auth.default()

client = Client(vertexai=True, project=project_id, location="global")


response = client.models.generate_content(
    model="gemini-flash-latest",
    contents="3 people like red, 2 people blue, 1 person likes green. Make this a pie chart. Return the chart as an image",
    config=types.GenerateContentConfig(
        system_instruction="You are a data visualzation agent. Your output should be an image.",
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


for part in response.candidates[0].content.parts:
    if part.inline_data:
        print(part.inline_data.as_image().save("pie.png"))

