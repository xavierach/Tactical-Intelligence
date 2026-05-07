from flask import Blueprint

from ..data.statsbomb_loader import list_competitions

competitions_bp = Blueprint("competitions", __name__)


@competitions_bp.get("/competitions")
def competitions() -> dict[str, list[dict[str, object]]]:
    return {"competitions": list_competitions()}
