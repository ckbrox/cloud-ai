from google.genai import Client, types
import google.auth
import json
import requests
import io

_, project_id = google.auth.default()
client = Client(vertexai=True, project=project_id, location="global")

image_path = "https://goo.gle/instrument-img"
image_bytes = requests.get(image_path).content
image = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")


response = client.models.generate_content(
    model="gemini-flash-latest",
    contents=[
        image,
        "Zoom into the expression pedals and tell me how many pedals are there?"
    ],
    config=types.GenerateContentConfig(
        system_instruction="Your output should be an image.",
        tools=[
            types.Tool(code_execution=types.ToolCodeExecution())
        ],
        temperature=0,
    ),
)


for part in response.candidates[0].content.parts:
    if part.text is not None:
        print(part.text)
    if part.executable_code is not None:
        print("# Code:")
        print(part.executable_code.code)
    if part.code_execution_result is not None:
        print("# Code Output:")
        print(part.code_execution_result.output)
    if part.as_image() is not None:
        print(part.inline_data.as_image().save("agentic_vision.png"))


print(response.model_dump_json(indent=4))