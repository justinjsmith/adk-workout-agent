"""ADK tools for validating parsed workouts."""

from __future__ import annotations

import json

from shared.schema import LaneIntervals, Workout, YardageEstimate

LANE_KEYS = ["L6", "L5", "L4", "L3", "L2", "L1"]
KNOWN_EQUIPMENT = {"Fins", "Paddles", "Pull Buoy"}


def _parse_lane_reps(lane_rep_counts: LaneIntervals | None, default_repeats: int) -> dict[str, int]:
    """Extract per-lane rep counts, falling back to default_repeats."""
    result = {}
    for lane in LANE_KEYS:
        val = getattr(lane_rep_counts, lane, None) if lane_rep_counts else None
        if val is not None:
            try:
                result[lane] = int(val)
            except (ValueError, TypeError):
                result[lane] = default_repeats
        else:
            result[lane] = default_repeats
    return result


def calculate_yardage(workout: Workout) -> YardageEstimate:
    """Calculate total yardage from parsed workout sections.

    Returns a YardageEstimate with:
    - estimated: sum of (repeats * distance) using default rep counts
    - by_lane: per-lane totals when any set has lane_rep_counts
    """
    estimated_total = 0
    lane_totals: dict[str, int] = {lane: 0 for lane in LANE_KEYS}
    has_lane_variation = False

    for section in workout.sections:
        for s in section.sets:
            if not s.distance:
                continue
            estimated_total += s.distance * s.repeats
            lane_reps = _parse_lane_reps(s.lane_rep_counts, s.repeats)
            for lane in LANE_KEYS:
                lane_totals[lane] += s.distance * lane_reps[lane]
            if s.lane_rep_counts:
                has_lane_variation = True

    by_lane = None
    if has_lane_variation:
        by_lane = LaneIntervals(**{lane: str(total) for lane, total in lane_totals.items()})

    return YardageEstimate(
        estimated=estimated_total if estimated_total > 0 else None,
        by_lane=by_lane,
    )


def validate_workout(workout_json: str) -> str:
    """Validate a parsed workout for structural completeness and reasonableness.

    Calculates total_yardage and includes it in the report so the agent can
    populate the field in the final workout object.

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
                warnings.append(f"Repeat count {s.repeats} in '{section.name}' seems very high.")

    # Check equipment consistency
    for section in workout.sections:
        ctx = section.equipment_context
        for s in section.sets:
            if ctx and not s.equipment:
                warnings.append(
                    f"Section '{section.name}' has equipment_context {ctx} but a set "
                    f"has empty equipment. Sets should inherit from equipment_context."
                )
                break  # One warning per section is enough
            if s.equipment and ctx and set(s.equipment) != set(ctx):
                warnings.append(
                    f"Section '{section.name}': set equipment {s.equipment} doesn't match "
                    f"equipment_context {ctx}."
                )
                break

        # Check for unknown equipment names
        all_equip = set(ctx)
        for s in section.sets:
            all_equip.update(s.equipment)
        unknown = all_equip - KNOWN_EQUIPMENT
        if unknown:
            warnings.append(
                f"Section '{section.name}' has unknown equipment: {sorted(unknown)}. "
                f"Known equipment: {sorted(KNOWN_EQUIPMENT)}."
            )

    # Calculate yardage
    yardage = calculate_yardage(workout)
    total = yardage.estimated or 0

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
        if yardage.by_lane:
            report_lines.append("\nPer-lane yardage:")
            for lane in LANE_KEYS:
                val = getattr(yardage.by_lane, lane)
                if val is not None:
                    report_lines.append(f"  {lane}: {val}y")

    report_lines.append("\n### total_yardage JSON (copy into workout)")
    report_lines.append(json.dumps(yardage.model_dump(exclude_none=True)))

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
