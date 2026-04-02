"""ADK Email Triage Agent — classifies whether an email contains a workout."""

from google.adk import Agent

from agent.prompts.parser import TRIAGE_SYSTEM_PROMPT
from shared.config import MODEL_HAIKU

triage_agent = Agent(
    name="email_triage",
    model=MODEL_HAIKU,
    description="Classifies coach emails as workout or non-workout.",
    instruction=TRIAGE_SYSTEM_PROMPT,
    tools=[],  # Triage doesn't need tools — it's a simple classifier
)
