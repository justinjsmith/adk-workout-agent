"""Tests for the Pydantic workout schema."""

from shared.schema import (
    ConventionsDoc,
    EffortProfileEntry,
    Flag,
    FlagType,
    Interval,
    IntervalType,
    LaneIntervals,
    Rest,
    RestType,
    Section,
    SetItem,
    Workout,
    WorkoutAnalysis,
    WorkoutStatus,
    WorkoutType,
    YardageEstimate,
)


def test_basic_set_item():
    s = SetItem(
        repeats=4,
        distance=75,
        distance_display="4x75",
        stroke="Kick",
        stroke_short="K",
        rest=Rest(type=RestType.REST, seconds=10, display="R:10"),
    )
    assert s.repeats == 4
    assert s.distance == 75
    assert s.stroke_short == "K"
    assert s.rest.seconds == 10


def test_range_interval():
    interval = Interval(
        type=IntervalType.RANGE,
        fast=":50",
        slow="1:10",
        display="@50-1:10",
    )
    assert interval.type == IntervalType.RANGE
    assert interval.fast == ":50"


def test_lane_intervals():
    li = LaneIntervals(L6="1:30", L5="1:35", L4="1:40", L3="1:45", L2="1:50", L1="2:00")
    assert li.L6 == "1:30"
    assert li.L1 == "2:00"


def test_section_with_sets():
    section = Section(
        name="Warm Up",
        sets=[
            SetItem(repeats=1, distance=400, stroke="Choice", stroke_short="Ch"),
            SetItem(
                repeats=4,
                distance=75,
                stroke="Kick",
                stroke_short="K",
                rest=Rest(type=RestType.REST, seconds=10),
            ),
        ],
    )
    assert section.name == "Warm Up"
    assert len(section.sets) == 2
    assert section.sets[1].rest.seconds == 10


def test_full_workout():
    workout = Workout(
        day_of_week="friday",
        workout_type=WorkoutType.SPRINT,
        status=WorkoutStatus.PENDING_REVIEW,
        confidence=0.85,
        flags=[
            Flag(type=FlagType.UNKNOWN_ABBREVIATION, text="TX", context="50K+50Sw TX"),
        ],
        sections=[
            Section(
                name="Warm Up",
                sets=[SetItem(repeats=1, distance=400, stroke="Choice")],
            ),
            Section(
                name="Main Set",
                sets=[
                    SetItem(
                        repeats=1,
                        distance=200,
                        stroke="Swim",
                        instruction="Fast In Heats",
                    ),
                ],
            ),
        ],
        total_yardage=YardageEstimate(estimated=4500),
    )
    assert workout.workout_type == WorkoutType.SPRINT
    assert len(workout.sections) == 2
    assert workout.flags[0].text == "TX"
    assert workout.total_yardage.estimated == 4500


def test_workout_json_roundtrip():
    workout = Workout(
        day_of_week="wednesday",
        workout_type=WorkoutType.THRESHOLD,
        sections=[
            Section(
                name="Main Set",
                sets=[
                    SetItem(
                        repeats=8,
                        distance=50,
                        stroke="Swim",
                        interval=Interval(type=IntervalType.RANGE, fast=":50", slow="1:10"),
                    ),
                ],
            ),
        ],
    )
    json_str = workout.model_dump_json()
    restored = Workout.model_validate_json(json_str)
    assert restored.workout_type == WorkoutType.THRESHOLD
    assert restored.sections[0].sets[0].interval.fast == ":50"


def test_conventions_doc():
    from shared.schema import Abbreviation, StructuralRule

    doc = ConventionsDoc(
        version=1,
        abbreviations={
            "Sw": Abbreviation(meaning="Swim", category="stroke_type"),
            "K": Abbreviation(meaning="Kick", category="stroke_type"),
        },
        structural_rules=[
            StructuralRule(rule="6 consecutive numbers = lane intervals L6-L1"),
        ],
    )
    assert doc.abbreviations["Sw"].meaning == "Swim"
    assert len(doc.structural_rules) == 1


def test_workout_analysis():
    analysis = WorkoutAnalysis(
        energy_systems=["aerobic", "anaerobic_threshold"],
        workout_narrative="This workout builds from an easy warm-up to threshold work.",
        coaching_intent="The descending rest trains lactate tolerance.",
        type_confidence=0.9,
        effort_profile=[
            EffortProfileEntry(section="Warm Up", intensity_pct=30, energy_system="aerobic"),
            EffortProfileEntry(
                section="Main Set",
                intensity_pct=80,
                energy_system="anaerobic_threshold",
            ),
            EffortProfileEntry(section="Warm Down", intensity_pct=25, energy_system="aerobic"),
        ],
    )
    assert len(analysis.energy_systems) == 2
    assert analysis.type_confidence == 0.9
    assert len(analysis.effort_profile) == 3
    assert analysis.effort_profile[1].intensity_pct == 80


def test_workout_with_analysis():
    workout = Workout(
        day_of_week="wednesday",
        workout_type=WorkoutType.THRESHOLD,
        confidence=0.85,
        sections=[
            Section(
                name="Main Set",
                sets=[SetItem(repeats=8, distance=100, stroke="Swim")],
            ),
        ],
        analysis=WorkoutAnalysis(
            energy_systems=["anaerobic_threshold"],
            workout_narrative="Threshold set.",
            coaching_intent="Build lactate clearance.",
            type_confidence=0.9,
            effort_profile=[
                EffortProfileEntry(
                    section="Main Set",
                    intensity_pct=80,
                    energy_system="anaerobic_threshold",
                ),
            ],
        ),
    )
    assert workout.analysis is not None
    assert workout.analysis.type_confidence == 0.9
    json_str = workout.model_dump_json()
    restored = Workout.model_validate_json(json_str)
    assert restored.analysis.energy_systems == ["anaerobic_threshold"]
