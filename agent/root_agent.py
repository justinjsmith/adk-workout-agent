"""Root ADK agent that orchestrates the email processing pipeline."""

from google.adk import Agent

from agent.parser_agent import parser_agent
from agent.triage_agent import triage_agent
from shared.config import MODEL_HAIKU

root_agent = Agent(
    name="workout_agent",
    model=MODEL_HAIKU,
    description="Root agent that orchestrates swim workout email processing.",
    instruction="""\
You are the orchestrator for the Stingrays swim workout email processing system.

When given an email, follow these steps:
1. Send the email to the email_triage agent to determine if it contains a workout.
2. If the email contains a workout, send the email body to the workout_parser agent to parse it.
3. If the email does not contain a workout, respond with a brief summary of what the email contains.

When given a direct command (e.g., "parse this workout text"), route it directly to the \
workout_parser agent without triage.
""",
    sub_agents=[triage_agent, parser_agent],
)
