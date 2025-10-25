from .tools.workday_tools import *
from google.adk.agents import LlmAgent, Agent
from a2a.types import AgentCard, AgentCapabilities, AgentSkill
from google.adk.tools import load_artifacts


class WorkdayAgent(LlmAgent):
    """An agent that can interact with Workday."""

    name: str = 'workday_agent'
    description: str = "An agent that can interact with Workday."

    def __init__(self, **kwargs):
        instructions = "You are a helpful agent who can answer user questions about using data from Workday. Today's date is {datetime.now().today().strftime('%Y-%m-%d')}. When using the request_time_off tool, users may give you a relative date. Use today's date to infer the full date."

        super().__init__(
            model='gemini-2.5-flash',
            instruction=instructions,
            tools=[
                search_workers,
                get_worker_timeoff,
                request_time_off,
                get_worker_details,
                get_org_chart,
                get_team_time_off_data,
                get_expenses,
                call_data_scientist_agent,
                get_team_details,
                load_artifacts
            ],
            **kwargs
        )

    def create_agent_card(self, agent_url: str) -> "AgentCard":
        return AgentCard(  
            name=self.name,
            description=self.description,
            url=agent_url,
            version="1.0.0",
            defaultInputModes=["text/plain"],
            defaultOutputModes=["text/plain"],
            capabilities=AgentCapabilities(streaming=True),
            skills=[
                AgentSkill(
                    id="workday",
                    name="Workday Skill",
                    description="Chat with the Workday agent.",
                    tags=["workday"],
                    examples=["how much time off?", "who is ____?", "can i take time off?", "what were my expenses?"]
                )
            ]

        )



