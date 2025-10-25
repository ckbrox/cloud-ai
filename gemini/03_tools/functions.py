from google.genai import Client, types 
import google.auth

_, project_id = google.auth.default()

client = Client(vertexai=True, project=project_id, location="global")

def get_current_weather(location: str = "Boston, MA"):
    """
    Get the current weather in a given location

    Args:
        location: The city name of the location for which to get the weather.

    """
    # This example uses a mock implementation.
    # You can define a local function or import the requests library to call an API
    
    return {
        "location": "Boston, MA",
        "temperature": 38,
        "description": "Partly Cloudy",
        "icon": "partly-cloudy",
        "humidity": 65,
        "wind": {
            "speed": 10,
            "direction": "NW"
        }
    }

def get_cuurent_traffic(location: str = "Boston, MA"):
    """
    Get the current traffic conditions in a given location

    Args:
        location: The city name of the location for which to get the traffic.

    """
    # This example uses a mock implementation.
    # You can define a local function or import the requests library to call an API
    return {
        "location": "Boston, MA",
        "conditions": "Moderate traffic",
        "average_speed": 25,
        "travel_time_to_downtown": "30 minutes"
    }


response = client.models.generate_content(
    model='gemini-flash-latest',
    contents=['What is the weather in Boston. Also what are the traffic conditions in Boston?'],
    config=types.GenerateContentConfig(
        tools=[
            get_current_weather, 
            get_cuurent_traffic
        ]
    )
)

print(response.model_dump_json(indent=4))

