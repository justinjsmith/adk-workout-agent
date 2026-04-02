"""ADK tools for validating parsed workouts."""

from __future__ import annotations

import json

from shared.schema import Workout


def validate_workout(workout_json: str) -> str:
    """Validate a parsed workout for structural completeness and reasonableness.

    Args:
        workout_json: JSON string of the parsed Workout object.

    Returns:
        Validation report as a string, listing any issues found.
    """
    try:
        data = json.loads(workout_json)
        workout = Workout(**data)
    except Exception as e:
        return f"VALIDATION ERROR: Could not parse workout JSON: {e}"

    issues = []
    warnings = []

    # Check basic structure
    if not workout.sections:
        issues.append("No sections found — workout appears empty.")

    # Check for warmup
    section_names = [s.name.lower() for s in workout.sections]
    has_warmup = any("warm" in n and ("up" in n or "down" not in n) for n in section_names)
    if not has_warmup:
        warnings.append("No Warm Up section detected.")

    has_warmdown = any("warm" in n and "down" in n for n in section_names)
    if not has_warmdown:
        warnings.append("No Warm Down section detected.")

    # Check distances are reasonable
    for section in workout.sections:
        for s in section.sets:
            if s.distance and s.distance > 2000:
                warnings.append(
                    f"Set distance {s.distance}y in '{section.name}' seems very long. "
                    f"Verify this is correct."
                )
            if s.repeats and s.repeats > 50:
                warnings.append(
                    f"Repeat count {s.repeats} in '{section.name}' seems very high."
                )

    # Estimate total yardage
    total = 0
    for section in workout.sections:
        for s in section.sets:
            if s.distance and s.repeats:
                total += s.distance * s.repeats

    if total > 0:
        if total < 1000:
            warnings.append(f"Total yardage estimate ({total}y) seems very low for a workout.")
        elif total > 8000:
            warnings.append(f"Total yardage estimate ({total}y) seems very high for a workout.")

    # Build report
    report_lines = ["## Validation Report", ""]

    if issues:
        report_lines.append("### Issues (must fix)")
        for issue in issues:
            report_lines.append(f"  ❌ {issue}")
        report_lines.append("")

    if warnings:
        report_lines.append("### Warnings (review)")
        for w in warnings:
            report_lines.append(f"  ⚠️ {w}")
        report_lines.append("")

    if not issues and not warnings:
        report_lines.append("✅ No issues found.")

    if total > 0:
        report_lines.append(f"\nEstimated total yardage: {total}y")

    return "\n".join(report_lines)


def flag_unknown(text: str, context: str, flag_type: str = "unknown_abbreviation") -> str:
    """Flag an unknown abbreviation or pattern for human review.

    Args:
        text: The unknown text (e.g., an abbreviation).
        context: Surrounding text that provides context.
        flag_type: Type of flag: "unknown_abbreviation" or "unknown_pattern".

    Returns:
        Confirmation message.
    """
    return (
        f"Flagged for review: '{text}' (type: {flag_type}). "
        f"Context: '{context}'. This will be shown to humans for clarification."
    )
