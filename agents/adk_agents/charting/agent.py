from google.adk.agents import Agent
from google.adk.tools import load_artifacts, ToolContext, VertexAiSearchTool, agent_tool
from google.genai import types
import base64
from google.genai import Client, types
import google.auth
import json

_, project_id = google.auth.default()

client = Client(vertexai=True, project=project_id, location="global")


async def charting_tool(question: str, tool_context: 'ToolContext'):
    '''
    Returns a chart based on a question with data

    Args:
        question (str): the question (and data) to chart

    Returns:
        dict: the chart as an image
    '''

    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=[question, 'Return the chart as an image'],
        config=types.GenerateContentConfig(
            system_instruction="You are a data visualzation agent. Your output should be an image.",
            tools=[
                types.Tool(code_execution=types.ToolCodeExecution())
            ],
            temperature=0,
        ),
    )
    
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            print(part.inline_data)
            
            await tool_context.save_artifact(filename='chart.png', artifact=part)

    return {
        'status': 'success',
        'message': f'The chart has been save as an artifact (chart.png)'
    }

root_agent = Agent(
    name="enterprise_search",
    instruction="You are a helpful agent who can search for content and answer questions about salesforce opportunities.",
    description="You job is to answer questions.",
    model="gemini-2.5-flash",
    tools=[
        load_artifacts,
        charting_tool
    ],
)