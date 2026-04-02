"""Tests for parser prompt content — ensures metadata extraction guidance is present."""

from agent.prompts.parser import PARSER_SYSTEM_PROMPT


def test_prompt_has_date_extraction_guidance():
    """Parser prompt must instruct the agent to extract date from email metadata."""
    assert "date" in PARSER_SYSTEM_PROMPT.lower()
    assert "day_of_week" in PARSER_SYSTEM_PROMPT
    assert "week_of" in PARSER_SYSTEM_PROMPT
    assert "Date Extraction" in PARSER_SYSTEM_PROMPT


def test_prompt_has_workout_type_classification():
    """Parser prompt must instruct the agent to classify workout type, not default to mixed."""
    assert "Workout Type Classification" in PARSER_SYSTEM_PROMPT
    assert "sprint" in PARSER_SYSTEM_PROMPT
    assert "threshold" in PARSER_SYSTEM_PROMPT
    assert "aerobic" in PARSER_SYSTEM_PROMPT
    assert "distance" in PARSER_SYSTEM_PROMPT
    # Must warn against defaulting to mixed
    assert "mixed" in PARSER_SYSTEM_PROMPT.lower()


def test_prompt_has_confidence_scoring():
    """Parser prompt must instruct the agent to score confidence, not leave at 0.0."""
    assert "Confidence Scoring" in PARSER_SYSTEM_PROMPT
    assert "0.0" in PARSER_SYSTEM_PROMPT
    assert "1.0" in PARSER_SYSTEM_PROMPT
    assert "Never leave it at 0.0" in PARSER_SYSTEM_PROMPT


def test_prompt_references_output_schema_fields():
    """Parser prompt must explicitly list the required output fields."""
    required_fields = [
        "date",
        "day_of_week",
        "week_of",
        "workout_type",
        "confidence",
        "email_message_id",
        "email_thread_id",
        "sections",
        "flags",
    ]
    for field in required_fields:
        assert field in PARSER_SYSTEM_PROMPT, f"Prompt missing required field: {field}"
