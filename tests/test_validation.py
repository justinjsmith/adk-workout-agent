"""Tests for workout validation tools."""

from agent.tools.validation import flag_unknown, validate_workout
from shared.schema import Section, SetItem, Workout, WorkoutType


def test_validate_empty_workout():
    workout = Workout()
    result = validate_workout(workout.model_dump_json())
    assert "No sections found" in result


def test_validate_valid_workout():
    workout = Workout(
        workout_type=WorkoutType.AEROBIC,
        sections=[
            Section(
                name="Warm Up",
                sets=[SetItem(repeats=1, distance=400, stroke="Choice")],
            ),
            Section(
                name="Main Set",
                sets=[
                    SetItem(repeats=10, distance=100, stroke="Swim"),
                    SetItem(repeats=4, distance=50, stroke="Kick"),
                ],
            ),
            Section(
                name="Warm Down",
                sets=[SetItem(repeats=1, distance=200, stroke="Choice")],
            ),
        ],
    )
    result = validate_workout(workout.model_dump_json())
    assert "No issues found" in result or "1600y" in result  # 400 + 1000 + 200 + ... = reasonable


def test_validate_high_yardage_warning():
    workout = Workout(
        sections=[
            Section(
                name="Main Set",
                sets=[SetItem(repeats=100, distance=100, stroke="Swim")],
            ),
        ],
    )
    result = validate_workout(workout.model_dump_json())
    # Should warn about very high yardage (10000y) or high repeat count
    assert "high" in result.lower() or "Warning" in result or "⚠️" in result


def test_validate_invalid_json():
    result = validate_workout("not valid json")
    assert "VALIDATION ERROR" in result


def test_flag_unknown():
    result = flag_unknown("TX", "50K+50Sw TX", "unknown_abbreviation")
    assert "TX" in result
    assert "flagged" in result.lower() or "Flagged" in result
