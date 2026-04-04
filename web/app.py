"""Flask web application for viewing parsed swim workouts."""

from __future__ import annotations

from flask import Flask, render_template, request

from shared.config import FLASK_SECRET_KEY
from web.storage import get_workout_by_id, get_workouts_by_week

LANE_KEYS = ["L6", "L5", "L4", "L3", "L2", "L1"]

TYPE_COLORS = {
    "aerobic": "#1976d2",
    "threshold": "#f57c00",
    "sprint": "#d32f2f",
    "distance": "#388e3c",
    "mixed": "#7b1fa2",
}


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = FLASK_SECRET_KEY

    @app.context_processor
    def inject_helpers():
        return {
            "lane_keys": LANE_KEYS,
            "type_colors": TYPE_COLORS,
        }

    @app.route("/health")
    def health():
        return {"status": "ok"}

    @app.route("/")
    def workout_list():
        weeks = get_workouts_by_week()
        return render_template("workout_list.html", weeks=weeks)

    @app.route("/workout/<workout_id>")
    def workout_detail(workout_id: str):
        workout = get_workout_by_id(workout_id)
        if not workout:
            return "Workout not found", 404
        lane = request.args.get("lane")
        return render_template("workout_detail.html", workout=workout, selected_lane=lane)

    @app.route("/workout/<workout_id>/print")
    def workout_print(workout_id: str):
        workout = get_workout_by_id(workout_id)
        if not workout:
            return "Workout not found", 404
        lane = request.args.get("lane")
        return render_template("workout_print.html", workout=workout, selected_lane=lane)

    return app
