"""ADK Workout Analyzer Agent — analyzes the physiology behind parsed workouts."""

from google.adk import Agent

from agent.prompts.analyzer import ANALYZER_SYSTEM_PROMPT
from shared.config import MODEL_SONNET

analyzer_agent = Agent(
    name="workout_analyzer",
    model=MODEL_SONNET,
    description="Analyzes parsed workouts for energy systems, coaching intent, and effort profile.",
    instruction=ANALYZER_SYSTEM_PROMPT,
    tools=[],
)
