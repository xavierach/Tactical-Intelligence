from __future__ import annotations

from typing import Any, Iterable


def analyze_player_impact(events: Iterable[dict[str, Any]] | None = None) -> dict[str, Any]:
    event_count = len(list(events or []))
    return {
        "summary": "Player impact scaffold.",
        "metrics": {
            "event_count": event_count,
            "xg_contribution": 0.0,
            "key_passes": 0,
            "possession_share": 0.0,
        },
        "players": [],
        "notes": [
            "Per-player contribution metrics will be aggregated here.",
            "This module should stay deterministic and analytics-first.",
        ],
    }
