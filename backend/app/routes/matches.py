from flask import Blueprint, request

from ..data.statsbomb_loader import list_matches

matches_bp = Blueprint("matches", __name__)


@matches_bp.get("/matches")
def matches() -> tuple[dict[str, object], int]:
    competition_id = request.args.get("competition_id", type=int)
    season_id = request.args.get("season_id", type=int)

    if competition_id is None or season_id is None:
        return {"error": "competition_id and season_id are required"}, 400

    return {"matches": list_matches(competition_id, season_id)}, 200
