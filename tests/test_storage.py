"""Tests for the dual-backend storage layer."""

from unittest.mock import patch

from shared.schema import Section, SetItem, Workout, WorkoutType


def _make_workout(**kwargs) -> Workout:
    defaults = {
        "id": "workout_test_001",
        "day_of_week": "monday",
        "workout_type": WorkoutType.AEROBIC,
        "confidence": 0.85,
        "sections": [
            Section(
                name="Warm Up",
                sets=[SetItem(repeats=1, distance=400, stroke="Choice")],
            ),
        ],
    }
    defaults.update(kwargs)
    return Workout(**defaults)


def test_store_and_get_local(tmp_path):
    """Store and retrieve a workout using local backend."""
    with (
        patch("agent.tools.storage.STORAGE_BACKEND", "local"),
        patch("agent.tools.storage.STORAGE_DIR", tmp_path),
    ):
        from agent.tools.storage import get_workout, store_workout

        workout = _make_workout()
        result = store_workout(workout.model_dump_json())
        assert "stored successfully" in result
        assert "workout_test_001" in result

        retrieved = get_workout("workout_test_001")
        assert retrieved is not None
        assert retrieved["id"] == "workout_test_001"
        assert retrieved["workout_type"] == "aerobic"


def test_get_all_workouts_local(tmp_path):
    """List workouts from local backend."""
    with (
        patch("agent.tools.storage.STORAGE_BACKEND", "local"),
        patch("agent.tools.storage.STORAGE_DIR", tmp_path),
    ):
        from agent.tools.storage import get_all_workouts, store_workout

        # Store two workouts
        w1 = _make_workout(id="workout_a")
        w2 = _make_workout(id="workout_b", workout_type=WorkoutType.SPRINT)
        store_workout(w1.model_dump_json())
        store_workout(w2.model_dump_json())

        workouts = get_all_workouts()
        assert len(workouts) == 2
        ids = {w["id"] for w in workouts}
        assert "workout_a" in ids
        assert "workout_b" in ids


def test_get_workout_not_found_local(tmp_path):
    """Return None for missing workout."""
    with (
        patch("agent.tools.storage.STORAGE_BACKEND", "local"),
        patch("agent.tools.storage.STORAGE_DIR", tmp_path),
    ):
        from agent.tools.storage import get_workout

        assert get_workout("nonexistent") is None


def test_store_workout_generates_id(tmp_path):
    """ID is auto-generated when missing."""
    with (
        patch("agent.tools.storage.STORAGE_BACKEND", "local"),
        patch("agent.tools.storage.STORAGE_DIR", tmp_path),
    ):
        from agent.tools.storage import store_workout

        workout = _make_workout(id=None)
        result = store_workout(workout.model_dump_json())
        assert "stored successfully" in result
        assert "workout_" in result


def test_store_workout_invalid_json():
    """Invalid JSON returns error."""
    from agent.tools.storage import store_workout

    result = store_workout("not valid json")
    assert "STORAGE ERROR" in result


def test_list_stored_workouts_empty(tmp_path):
    """Empty storage returns message."""
    with (
        patch("agent.tools.storage.STORAGE_BACKEND", "local"),
        patch("agent.tools.storage.STORAGE_DIR", tmp_path),
    ):
        from agent.tools.storage import list_stored_workouts

        result = list_stored_workouts()
        assert "No workouts" in result
