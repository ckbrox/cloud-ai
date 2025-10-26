from google.cloud.aiplatform_v1beta1.types import Tool as VertexTool
from langchain_google_vertexai import ChatVertexAI

llm = ChatVertexAI(model="gemini-2.5-flash")
resp = llm.invoke(
    "When is the next total solar eclipse in US?",
    tools=[VertexTool(google_search={})],
)

print(resp)
