from flask import Blueprint

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ai-tactical-report-generator",
    }
