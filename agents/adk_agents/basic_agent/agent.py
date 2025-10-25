from google.adk.agents import Agent
from google.genai import Client, types

import google.auth

_, project_id = google.auth.default()

client = Client(vertexai=True, project=project_id, location="global")


def get_weather(location: str):
    '''
    Gets the weather for a given location. Make sure to include the citations when using this tool.
    Args:
        location (str): The location to get the weather for.
    Returns:
        dict: The weather for the given location.
    '''
    response = client.models.generate_content(
        model='gemini-flash-latest',
        contents=[f'What is the weather in {location}'],
        config=types.GenerateContentConfig( 
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )
    return response.model_dump_json()


root_agent = Agent(
    name="basic_agent",
    instruction="You are a helpful assistant",
    model='gemini-flash-lite-latest',
    tools=[
        get_weather
    ]
)