"""ADK tools for loading conventions and managing the knowledge base."""

from __future__ import annotations

import json
from pathlib import Path

from shared.schema import ConventionsDoc

CONVENTIONS_SEED = Path(__file__).resolve().parent.parent.parent / "conventions" / "seed.json"

# In-memory cache of conventions (later replaced by Firestore)
_conventions_cache: ConventionsDoc | None = None


def _load_conventions_from_seed() -> ConventionsDoc:
    """Load conventions from the seed JSON file."""
    data = json.loads(CONVENTIONS_SEED.read_text())

    # Transform the flat JSON into ConventionsDoc structure
    from shared.schema import (
        Abbreviation,
        StructuralRule,
        WorkoutTypeHeuristic,
    )

    abbrevs = {}
    for key, val in data.get("abbreviations", {}).items():
        abbrevs[key] = Abbreviation(**val)

    rules = [StructuralRule(**r) for r in data.get("structuralRules", [])]
    heuristics = [WorkoutTypeHeuristic(**h) for h in data.get("workoutTypeHeuristics", [])]

    return ConventionsDoc(
        version=data.get("version", 1),
        abbreviations=abbrevs,
        structural_rules=rules,
        workout_type_heuristics=heuristics,
    )


def get_conventions_text() -> str:
    """Return conventions as formatted text for embedding in prompts.

    This is used to pre-load conventions into the parser prompt,
    eliminating the need for a tool call at runtime.
    """
    global _conventions_cache
    if _conventions_cache is None:
        _conventions_cache = _load_conventions_from_seed()

    doc = _conventions_cache

    lines = [f"# Conventions (version {doc.version})", ""]

    lines.append("## Abbreviations")
    for abbr, info in sorted(doc.abbreviations.items()):
        lines.append(f"  {abbr} = {info.meaning} ({info.category})")
    lines.append("")

    lines.append("## Structural Rules")
    for rule in doc.structural_rules:
        lines.append(f"  - {rule.rule}")
    lines.append("")

    lines.append("## Workout Type Heuristics")
    for h in doc.workout_type_heuristics:
        lines.append(f"  - '{h.pattern}' → {h.suggests_type}")

    return "\n".join(lines)


def load_conventions() -> str:
    """Load the current conventions document.

    Returns the conventions as a formatted string for the agent to use.
    In Phase 1 this loads from the seed file; later it will load from Firestore.
    """
    return get_conventions_text()


def lookup_abbreviation(abbreviation: str) -> str:
    """Look up a specific abbreviation in the conventions doc.

    Args:
        abbreviation: The abbreviation to look up (e.g., "TX", "LB").

    Returns:
        The meaning and details if found, or a message indicating it's unknown.
    """
    global _conventions_cache
    if _conventions_cache is None:
        _conventions_cache = _load_conventions_from_seed()

    doc = _conventions_cache
    info = doc.abbreviations.get(abbreviation)
    if info:
        return (
            f"{abbreviation} = {info.meaning} "
            f"(category: {info.category}, confidence: {info.confidence})"
        )
    return f"Unknown abbreviation: '{abbreviation}'. Consider calling flag_unknown."
