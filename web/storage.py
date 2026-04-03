"""Storage access layer for the web app.

Thin wrapper around agent.tools.storage that adds grouping and formatting
helpers for template rendering.
"""

from __future__ import annotations

from collections import defaultdict

from agent.tools.storage import get_all_workouts, get_workout


def get_workouts_by_week(limit: int = 50) -> list[dict]:
    """Get workouts grouped by week_of, most recent first.

    Returns:
        List of dicts: [{"week_of": "2026-03-30", "workouts": [...]}, ...]
    """
    workouts = get_all_workouts(limit)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for w in workouts:
        week = str(w.get("week_of", "unknown"))
        grouped[week].append(w)

    # Sort weeks descending
    result = []
    for week in sorted(grouped.keys(), reverse=True):
        result.append({"week_of": week, "workouts": grouped[week]})
    return result


def get_workout_by_id(workout_id: str) -> dict | None:
    """Get a single workout by ID."""
    return get_workout(workout_id)
