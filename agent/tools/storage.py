"""ADK tools for storing parsed workouts.

Phase 1: Local JSON file storage.
Phase 2+: Firestore.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from shared.schema import Workout

STORAGE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "workouts"


def store_workout(workout_json: str) -> str:
    """Store a parsed workout.

    Args:
        workout_json: JSON string of the parsed Workout object.

    Returns:
        Confirmation message with the storage location/ID.
    """
    try:
        data = json.loads(workout_json)
        workout = Workout(**data)
    except Exception as e:
        return f"STORAGE ERROR: Could not parse workout JSON: {e}"

    # Generate an ID if not present
    if not workout.id:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        date_part = workout.date.isoformat() if workout.date else "unknown"
        workout.id = f"workout_{date_part}_{ts}"

    # Phase 1: Store as local JSON file
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    filepath = STORAGE_DIR / f"{workout.id}.json"
    filepath.write_text(workout.model_dump_json(indent=2))

    return f"Workout stored successfully: {workout.id} → {filepath}"


def list_stored_workouts() -> str:
    """List all stored workouts.

    Returns:
        Summary of stored workouts.
    """
    if not STORAGE_DIR.exists():
        return "No workouts stored yet."

    files = sorted(STORAGE_DIR.glob("*.json"), reverse=True)
    if not files:
        return "No workouts stored yet."

    lines = [f"Found {len(files)} stored workouts:", ""]
    for f in files[:20]:  # Show at most 20
        try:
            data = json.loads(f.read_text())
            date_str = data.get("date", "?")
            wtype = data.get("workout_type", "?")
            status = data.get("status", "?")
            lines.append(f"  {f.stem}: {date_str} ({wtype}) [{status}]")
        except Exception:
            lines.append(f"  {f.stem}: (error reading)")

    return "\n".join(lines)
