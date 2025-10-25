from google.adk.agents import Agent
from .twilio_client import TwilioClient

twilio_client = TwilioClient()

root_agent = Agent(
    name="twilio_agent",
    instruction="You are a helpful assistant",
    model='gemini-flash-lite-latest',
    tools=[
        twilio_client.send_outbound_sms
    ]
)