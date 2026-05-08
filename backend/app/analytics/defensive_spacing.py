from __future__ import annotations

from collections import Counter
from itertools import combinations
from math import sqrt
from typing import Any, Iterable


PITCH_LENGTH = 120.0
PITCH_WIDTH = 80.0
PITCH_DIAGONAL = sqrt(PITCH_LENGTH**2 + PITCH_WIDTH**2)
DEFENSIVE_EVENT_TYPES = {
    "pressure",
    "tackle",
    "interception",
    "block",
    "clearance",
    "ball recovery",
    "dispossessed",
    "duel",
}


def _string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        for candidate in ("name", "value", "player_name", "team_name"):
            nested = value.get(candidate)
            if nested:
                return str(nested)
        return ""
    return str(value)


def _event_type(event: dict[str, Any]) -> str:
    return _string(
        event.get("type")
        or event.get("event_type")
        or event.get("type_name")
        or event.get("sub_type")
    ).lower()


def _team_name(event: dict[str, Any]) -> str:
    return _string(event.get("team") or event.get("team_name"))


def _location(event: dict[str, Any]) -> tuple[float, float] | None:
    location = event.get("location")
    if isinstance(location, dict):
        x = location.get("x")
        y = location.get("y")
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            return float(x), float(y)
    elif isinstance(location, (list, tuple)) and len(location) >= 2:
        x, y = location[0], location[1]
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            return float(x), float(y)

    x_value = event.get("x")
    y_value = event.get("y")
    if isinstance(x_value, (int, float)) and isinstance(y_value, (int, float)):
        return float(x_value), float(y_value)

    return None


def _average_pairwise_distance(points: list[tuple[float, float]]) -> float:
    if len(points) < 2:
        return 0.0
    distances = [
        sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
        for (x1, y1), (x2, y2) in combinations(points, 2)
    ]
    return sum(distances) / len(distances)


def _largest_coordinate_gaps(values: list[float]) -> list[dict[str, Any]]:
    if len(values) < 2:
        return []

    sorted_values = sorted(values)
    gaps = []
    for left, right in zip(sorted_values, sorted_values[1:]):
        gap = right - left
        gaps.append(
            {
                "start": round(left, 2),
                "end": round(right, 2),
                "gap": round(gap, 2),
            }
        )
    gaps.sort(key=lambda item: item["gap"], reverse=True)
    return gaps[:3]


def analyze_defensive_spacing(events: Iterable[dict[str, Any]] | None = None) -> dict[str, Any]:
    event_list = list(events or [])
    defensive_events = [
        event
        for event in event_list
        if _event_type(event) in DEFENSIVE_EVENT_TYPES and _location(event) is not None
    ]

    if not defensive_events:
        return {
            "summary": "No defensive actions with usable locations were available.",
            "metrics": {
                "event_count": len(event_list),
                "defensive_action_count": 0,
                "line_stretch": 0.0,
                "compactness": 0.0,
            },
            "team_breakdown": [],
            "gaps": [],
            "notes": [
                "Add defensive action locations to calculate spatial compactness and line stretch.",
            ],
        }

    team_counts = Counter(_team_name(event) or "Unknown Team" for event in defensive_events)
    dominant_team, dominant_count = team_counts.most_common(1)[0]
    team_defensive_events = [
        event for event in defensive_events if (_team_name(event) or "Unknown Team") == dominant_team
    ]
    if not team_defensive_events:
        team_defensive_events = defensive_events
        dominant_team = "Unknown Team"
        dominant_count = len(team_defensive_events)

    positions = [_location(event) for event in team_defensive_events]
    positions = [position for position in positions if position is not None]

    xs = [point[0] for point in positions]
    ys = [point[1] for point in positions]
    x_range = max(xs) - min(xs) if xs else 0.0
    y_range = max(ys) - min(ys) if ys else 0.0

    avg_pairwise_distance = _average_pairwise_distance(positions)
    average_distance_norm = min(avg_pairwise_distance / PITCH_DIAGONAL, 1.0)
    compactness = round(max(0.0, 1.0 - average_distance_norm), 3)

    line_stretch_x = min(x_range / PITCH_LENGTH, 1.0)
    line_stretch_y = min(y_range / PITCH_WIDTH, 1.0)
    line_stretch = round((line_stretch_x + line_stretch_y) / 2.0, 3)

    centroid_x = round(sum(xs) / len(xs), 2) if xs else 0.0
    centroid_y = round(sum(ys) / len(ys), 2) if ys else 0.0

    team_breakdown = [
        {
            "team": team,
            "defensive_actions": count,
            "share": round(count / len(defensive_events), 3),
        }
        for team, count in team_counts.most_common()
    ]

    gaps = [
        {
            "axis": "x",
            "team": dominant_team,
            "gaps": _largest_coordinate_gaps(xs),
        },
        {
            "axis": "y",
            "team": dominant_team,
            "gaps": _largest_coordinate_gaps(ys),
        },
    ]

    summary = (
        f"{dominant_team} produced {dominant_count} defensive actions with a compactness score "
        f"of {compactness:.2f} and line stretch of {line_stretch:.2f}."
    )

    return {
        "summary": summary,
        "metrics": {
            "event_count": len(event_list),
            "defensive_action_count": len(defensive_events),
            "dominant_team_defensive_count": dominant_count,
            "line_stretch": line_stretch,
            "compactness": compactness,
            "centroid_x": centroid_x,
            "centroid_y": centroid_y,
        },
        "team_breakdown": team_breakdown,
        "gaps": gaps,
        "notes": [
            "Compactness is derived from the average pairwise distance between defensive actions.",
            "Line stretch combines the vertical and horizontal spread of defensive actions.",
            "The dominant defending team is chosen by the number of defensive actions with locations.",
        ],
    }
