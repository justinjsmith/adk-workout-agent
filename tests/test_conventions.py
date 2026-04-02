"""Tests for conventions loading."""

from agent.tools.conventions import load_conventions, lookup_abbreviation


def test_load_conventions_returns_string():
    result = load_conventions()
    assert isinstance(result, str)
    assert "Abbreviations" in result
    assert "Sw = Swim" in result
    assert "Structural Rules" in result


def test_lookup_known_abbreviation():
    result = lookup_abbreviation("Sw")
    assert "Swim" in result
    assert "stroke_type" in result


def test_lookup_unknown_abbreviation():
    result = lookup_abbreviation("XYZ")
    assert "Unknown" in result
    assert "flag_unknown" in result


def test_conventions_has_all_seed_abbreviations():
    result = load_conventions()
    # Check a sample of expected abbreviations
    for abbr in ["Sw", "K", "P", "Ch", "Fr", "IM", "ST", "Fins", "LB", "AR"]:
        assert abbr in result, f"Missing abbreviation: {abbr}"
