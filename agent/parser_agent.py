"""ADK Workout Parser Agent — the core agent that parses swim workout emails."""

from google.adk import Agent

from agent.prompts.parser import PARSER_SYSTEM_PROMPT
from agent.tools.conventions import load_conventions, lookup_abbreviation
from agent.tools.storage import store_workout
from agent.tools.validation import flag_unknown, validate_workout
from shared.config import MODEL_SONNET

parser_agent = Agent(
    name="workout_parser",
    model=MODEL_SONNET,
    description="Parses swim workout emails into structured JSON format.",
    instruction=PARSER_SYSTEM_PROMPT,
    tools=[
        load_conventions,
        lookup_abbreviation,
        validate_workout,
        flag_unknown,
        store_workout,
    ],
)
