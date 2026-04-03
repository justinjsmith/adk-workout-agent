"""Tests for analyzer prompt content — ensures physiological analysis guidance is present."""

from agent.prompts.analyzer import ANALYZER_SYSTEM_PROMPT


def test_prompt_has_energy_system_classification():
    """Analyzer prompt must define the energy system categories."""
    assert "atp_cp" in ANALYZER_SYSTEM_PROMPT
    assert "anaerobic_glycolytic" in ANALYZER_SYSTEM_PROMPT
    assert "aerobic" in ANALYZER_SYSTEM_PROMPT
    assert "anaerobic_threshold" in ANALYZER_SYSTEM_PROMPT


def test_prompt_has_workout_narrative_guidance():
    """Analyzer prompt must instruct on workout narrative generation."""
    assert "Workout Narrative" in ANALYZER_SYSTEM_PROMPT
    assert "training arc" in ANALYZER_SYSTEM_PROMPT


def test_prompt_has_coaching_intent_guidance():
    """Analyzer prompt must instruct on coaching intent inference."""
    assert "Coaching Intent" in ANALYZER_SYSTEM_PROMPT
    assert "Descending distance" in ANALYZER_SYSTEM_PROMPT


def test_prompt_has_type_validation():
    """Analyzer prompt must instruct on validating the parser's workout type."""
    assert "Type Validation" in ANALYZER_SYSTEM_PROMPT
    assert "type_confidence" in ANALYZER_SYSTEM_PROMPT


def test_prompt_has_effort_profile_guidance():
    """Analyzer prompt must define effort profile output."""
    assert "Effort Profile" in ANALYZER_SYSTEM_PROMPT
    assert "intensity_pct" in ANALYZER_SYSTEM_PROMPT
    assert "energy_system" in ANALYZER_SYSTEM_PROMPT


def test_prompt_has_output_schema():
    """Analyzer prompt must include the expected output JSON schema."""
    assert "energy_systems" in ANALYZER_SYSTEM_PROMPT
    assert "workout_narrative" in ANALYZER_SYSTEM_PROMPT
    assert "coaching_intent" in ANALYZER_SYSTEM_PROMPT
    assert "effort_profile" in ANALYZER_SYSTEM_PROMPT
