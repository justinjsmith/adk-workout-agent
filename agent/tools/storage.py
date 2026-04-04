"""ADK tools for storing parsed workouts.

Supports two backends controlled by STORAGE_BACKEND env var:
- "local" (default): JSON files in data/workouts/
- "firestore": Google Cloud Firestore workouts collection
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from shared.config import STORAGE_BACKEND
from shared.schema import Workout

STORAGE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "workouts"
WORKOUTS_COLLECTION = "workouts"


# --- Backend helpers ---


def _store_local(workout: Workout) -> str:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    filepath = STORAGE_DIR / f"{workout.id}.json"
    filepath.write_text(workout.model_dump_json(indent=2))
    return f"Workout stored successfully: {workout.id} → {filepath}"


def _store_firestore(workout: Workout) -> str:
    from shared.firestore import get_firestore_client

    db = get_firestore_client()
    doc_ref = db.collection(WORKOUTS_COLLECTION).document(workout.id)
    doc_ref.set(workout.model_dump(mode="json"))
    return (
        f"Workout stored successfully: {workout.id} → firestore:{WORKOUTS_COLLECTION}/{workout.id}"
    )


def _list_local(limit: int = 50) -> list[dict]:
    if not STORAGE_DIR.exists():
        return []
    files = sorted(STORAGE_DIR.glob("*.json"), reverse=True)
    results = []
    for f in files[:limit]:
        try:
            results.append(json.loads(f.read_text()))
        except Exception:
            continue
    return results


def _list_firestore(limit: int = 50) -> list[dict]:
    from shared.firestore import get_firestore_client

    db = get_firestore_client()
    query = db.collection(WORKOUTS_COLLECTION).order_by("date", direction="DESCENDING").limit(limit)
    return [doc.to_dict() for doc in query.stream()]


def _get_local(workout_id: str) -> dict | None:
    filepath = STORAGE_DIR / f"{workout_id}.json"
    if not filepath.exists():
        return None
    try:
        return json.loads(filepath.read_text())
    except Exception:
        return None


def _get_firestore(workout_id: str) -> dict | None:
    from shared.firestore import get_firestore_client

    db = get_firestore_client()
    doc = db.collection(WORKOUTS_COLLECTION).document(workout_id).get()
    if doc.exists:
        return doc.to_dict()
    return None


# --- Public API ---


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

    if STORAGE_BACKEND == "firestore":
        return _store_firestore(workout)
    return _store_local(workout)


def list_stored_workouts() -> str:
    """List all stored workouts.

    Returns:
        Summary of stored workouts.
    """
    workouts = get_all_workouts()
    if not workouts:
        return "No workouts stored yet."

    lines = [f"Found {len(workouts)} stored workouts:", ""]
    for data in workouts[:20]:
        wid = data.get("id", "?")
        date_str = data.get("date", "?")
        wtype = data.get("workout_type", "?")
        status = data.get("status", "?")
        lines.append(f"  {wid}: {date_str} ({wtype}) [{status}]")

    return "\n".join(lines)


def get_workout(workout_id: str) -> dict | None:
    """Get a single workout by ID.

    Returns:
        Workout dict or None if not found.
    """
    if STORAGE_BACKEND == "firestore":
        return _get_firestore(workout_id)
    return _get_local(workout_id)


def get_all_workouts(limit: int = 50) -> list[dict]:
    """Get all workouts, most recent first.

    Returns:
        List of workout dicts.
    """
    if STORAGE_BACKEND == "firestore":
        return _list_firestore(limit)
    return _list_local(limit)
