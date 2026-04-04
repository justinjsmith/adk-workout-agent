"""Tests for the Flask web application."""

from unittest.mock import patch

import pytest


def _sample_workout_dict(**kwargs):
    defaults = {
        "id": "workout_2026-03-31_test",
        "date": "2026-03-31",
        "day_of_week": "tuesday",
        "week_of": "2026-03-30",
        "workout_type": "aerobic",
        "confidence": 0.85,
        "status": "pending_review",
        "flags": [],
        "sections": [
            {
                "name": "Warm Up",
                "equipment_context": [],
                "sets": [
                    {
                        "repeats": 1,
                        "distance": 400,
                        "distance_display": "400",
                        "stroke": "Choice",
                        "stroke_short": "Ch",
                        "equipment": [],
                        "interval": None,
                        "rest": None,
                        "instruction": None,
                        "raw_text": "400 Ch",
                    }
                ],
            },
            {
                "name": "Main Set",
                "equipment_context": [],
                "sets": [
                    {
                        "repeats": 8,
                        "distance": 50,
                        "distance_display": "8x50",
                        "stroke": "Swim",
                        "stroke_short": "Sw",
                        "equipment": [],
                        "interval": {"type": "flat", "value": "1:00", "display": "@1:00"},
                        "rest": None,
                        "instruction": "Build",
                        "lane_intervals": {
                            "L6": ":50",
                            "L5": ":55",
                            "L4": "1:00",
                            "L3": "1:05",
                            "L2": "1:10",
                            "L1": "1:15",
                        },
                        "raw_text": "8x50 Sw Build",
                    }
                ],
            },
        ],
        "variants": [],
        "total_yardage": {"estimated": 4500},
    }
    defaults.update(kwargs)
    return defaults


@pytest.fixture
def app():
    from web.app import create_app

    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_health_endpoint(client):
    """Health endpoint returns ok for Cloud Run probes."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json == {"status": "ok"}


def test_workout_list_empty(client):
    """Empty list shows empty state."""
    with patch("web.app.get_workouts_by_week", return_value=[]):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"No workouts" in resp.data


def test_workout_list_with_data(client):
    """List page shows workouts grouped by week."""
    weeks = [{"week_of": "2026-03-30", "workouts": [_sample_workout_dict()]}]
    with patch("web.app.get_workouts_by_week", return_value=weeks):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"2026-03-30" in resp.data
        assert b"aerobic" in resp.data


def test_workout_detail(client):
    """Detail page renders workout sections."""
    workout = _sample_workout_dict()
    with patch("web.app.get_workout_by_id", return_value=workout):
        resp = client.get("/workout/workout_2026-03-31_test")
        assert resp.status_code == 200
        assert b"Warm Up" in resp.data
        assert b"Main Set" in resp.data
        assert b"Build" in resp.data


def test_workout_detail_not_found(client):
    """404 for missing workout."""
    with patch("web.app.get_workout_by_id", return_value=None):
        resp = client.get("/workout/nonexistent")
        assert resp.status_code == 404


def test_workout_detail_with_lane_filter(client):
    """Lane filter selects specific lane."""
    workout = _sample_workout_dict()
    with patch("web.app.get_workout_by_id", return_value=workout):
        resp = client.get("/workout/workout_2026-03-31_test?lane=L4")
        assert resp.status_code == 200
        assert b"L4" in resp.data


def test_workout_print(client):
    """Print page renders successfully."""
    workout = _sample_workout_dict()
    with patch("web.app.get_workout_by_id", return_value=workout):
        resp = client.get("/workout/workout_2026-03-31_test/print")
        assert resp.status_code == 200
        assert b"Stingrays" in resp.data
        assert b"Warm Up" in resp.data


def test_workout_print_with_lane(client):
    """Print page filters to specific lane."""
    workout = _sample_workout_dict()
    with patch("web.app.get_workout_by_id", return_value=workout):
        resp = client.get("/workout/workout_2026-03-31_test/print?lane=L6")
        assert resp.status_code == 200
        assert b"L6" in resp.data
