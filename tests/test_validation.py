"""Tests for workout validation tools."""

from agent.tools.validation import calculate_yardage, flag_unknown, validate_workout
from shared.schema import LaneIntervals, Section, SetItem, Workout, WorkoutType


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


def test_calculate_yardage_basic():
    workout = Workout(
        sections=[
            Section(
                name="Warm Up",
                sets=[SetItem(repeats=1, distance=400)],
            ),
            Section(
                name="Main Set",
                sets=[
                    SetItem(repeats=10, distance=100),
                    SetItem(repeats=4, distance=50),
                ],
            ),
        ],
    )
    yardage = calculate_yardage(workout)
    assert yardage.estimated == 1600  # 400 + 1000 + 200
    assert yardage.by_lane is None  # No lane variation


def test_calculate_yardage_with_lane_rep_counts():
    workout = Workout(
        sections=[
            Section(
                name="Main Set",
                sets=[
                    SetItem(
                        repeats=6,
                        distance=100,
                        lane_rep_counts=LaneIntervals(
                            L6="6",
                            L5="6",
                            L4="5",
                            L3="5",
                            L2="4",
                            L1="3",
                        ),
                    ),
                ],
            ),
        ],
    )
    yardage = calculate_yardage(workout)
    assert yardage.estimated == 600  # 6 * 100 (default repeats)
    assert yardage.by_lane is not None
    assert yardage.by_lane.L6 == "600"
    assert yardage.by_lane.L1 == "300"
    assert yardage.by_lane.L4 == "500"


def test_calculate_yardage_mixed_sets():
    """Sets with and without lane_rep_counts."""
    workout = Workout(
        sections=[
            Section(
                name="Warm Up",
                sets=[SetItem(repeats=1, distance=400)],
            ),
            Section(
                name="Main Set",
                sets=[
                    SetItem(
                        repeats=6,
                        distance=100,
                        lane_rep_counts=LaneIntervals(
                            L6="6",
                            L5="6",
                            L4="5",
                            L3="5",
                            L2="4",
                            L1="3",
                        ),
                    ),
                ],
            ),
        ],
    )
    yardage = calculate_yardage(workout)
    assert yardage.estimated == 1000  # 400 + 600
    assert yardage.by_lane is not None
    # Warm up: 400 for all lanes. Main set: varies.
    assert yardage.by_lane.L6 == "1000"  # 400 + 600
    assert yardage.by_lane.L1 == "700"  # 400 + 300


def test_calculate_yardage_no_distance():
    workout = Workout(
        sections=[
            Section(
                name="Main Set",
                sets=[SetItem(repeats=4)],  # No distance
            ),
        ],
    )
    yardage = calculate_yardage(workout)
    assert yardage.estimated is None
    assert yardage.by_lane is None


def test_validate_workout_includes_yardage_json():
    workout = Workout(
        sections=[
            Section(
                name="Main Set",
                sets=[SetItem(repeats=10, distance=100)],
            ),
        ],
    )
    result = validate_workout(workout.model_dump_json())
    assert "total_yardage JSON" in result
    assert '"estimated": 1000' in result


def test_validate_equipment_context_without_set_equipment():
    """Warn when section has equipment_context but sets have empty equipment."""
    workout = Workout(
        sections=[
            Section(
                name="Fins Set",
                equipment_context=["Fins"],
                sets=[SetItem(repeats=3, distance=100, stroke="Kick", equipment=[])],
            ),
        ],
    )
    result = validate_workout(workout.model_dump_json())
    assert "equipment_context" in result
    assert "empty equipment" in result


def test_validate_equipment_consistent():
    """No equipment warnings when section context matches set equipment."""
    workout = Workout(
        workout_type=WorkoutType.AEROBIC,
        sections=[
            Section(
                name="Warm Up",
                sets=[SetItem(repeats=1, distance=400, stroke="Choice")],
            ),
            Section(
                name="Fins Kick",
                equipment_context=["Fins"],
                sets=[
                    SetItem(repeats=3, distance=100, stroke="Kick", equipment=["Fins"]),
                ],
            ),
            Section(
                name="Warm Down",
                sets=[SetItem(repeats=1, distance=200, stroke="Choice")],
            ),
        ],
    )
    result = validate_workout(workout.model_dump_json())
    assert "equipment_context" not in result
    assert "empty equipment" not in result


def test_validate_equipment_mismatch():
    """Warn when set equipment doesn't match section equipment_context."""
    workout = Workout(
        sections=[
            Section(
                name="Paddles Set",
                equipment_context=["Paddles"],
                sets=[
                    SetItem(
                        repeats=4, distance=75, stroke="Swim",
                        equipment=["Fins"],  # Mismatch!
                    ),
                ],
            ),
        ],
    )
    result = validate_workout(workout.model_dump_json())
    assert "doesn't match" in result or "doesn't match" in result.replace("\u2019", "'")


def test_validate_unknown_equipment():
    """Warn when equipment names are not in the known set."""
    workout = Workout(
        sections=[
            Section(
                name="Snorkel Set",
                equipment_context=["Snorkel"],
                sets=[
                    SetItem(
                        repeats=4, distance=100, stroke="Swim",
                        equipment=["Snorkel"],
                    ),
                ],
            ),
        ],
    )
    result = validate_workout(workout.model_dump_json())
    assert "unknown equipment" in result.lower()
    assert "Snorkel" in result


def test_flag_unknown():
    result = flag_unknown("TX", "50K+50Sw TX", "unknown_abbreviation")
    assert "TX" in result
    assert "flagged" in result.lower() or "Flagged" in result
