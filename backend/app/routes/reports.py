from flask import Blueprint, request

from ..data.statsbomb_loader import load_match_events
from ..domain import MatchContext
from ..reporting.generator import generate_tactical_report

reports_bp = Blueprint("reports", __name__)


@reports_bp.post("/reports/generate")
def generate_report() -> tuple[dict[str, object], int]:
    payload = request.get_json(silent=True) or {}
    match_payload = payload.get("match") or {}
    match_id = str(match_payload.get("match_id") or payload.get("match_id") or "")
    if not match_id:
        return {"error": "match_id is required"}, 400

    focus_team = str(
        payload.get("focus_team")
        or match_payload.get("focus_team")
        or match_payload.get("home_team")
        or "Home Team"
    )

    match = MatchContext(
        match_id=match_id,
        competition=str(
            match_payload.get("competition_name")
            or match_payload.get("competition")
            or "StatsBomb Open Data"
        ),
        season=str(match_payload.get("season_name") or match_payload.get("season") or ""),
        home_team=str(match_payload.get("home_team") or "Home Team"),
        away_team=str(match_payload.get("away_team") or "Away Team"),
        focus_team=focus_team,
        kickoff=str(match_payload.get("match_date") or match_payload.get("kick_off") or ""),
        venue=payload.get("venue"),
    )

    events = load_match_events(match.match_id)

    report = generate_tactical_report(match, events)
    return {"report": report.to_dict()}, 200
