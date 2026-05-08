from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Iterable


TRANSITION_DURATION_THRESHOLD = 8.0
TRANSITION_LENGTH_THRESHOLD = 4


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


def _possession_id(event: dict[str, Any], fallback: int) -> int:
    possession = event.get("possession") or event.get("possession_id")
    if isinstance(possession, (int, float)):
        return int(possession)
    return fallback


def _seconds(event: dict[str, Any]) -> float:
    minute = event.get("minute")
    second = event.get("second")
    if isinstance(minute, (int, float)) and isinstance(second, (int, float)):
        return float(minute) * 60.0 + float(second)

    timestamp = event.get("timestamp")
    if isinstance(timestamp, str) and timestamp:
        try:
            parsed = datetime.strptime(timestamp.split(".")[0], "%H:%M:%S")
            return float(parsed.hour * 3600 + parsed.minute * 60 + parsed.second)
        except ValueError:
            return 0.0

    time_seconds = event.get("time_seconds")
    if isinstance(time_seconds, (int, float)):
        return float(time_seconds)

    return 0.0


def _location_x(event: dict[str, Any]) -> float | None:
    location = event.get("location")
    if isinstance(location, (list, tuple)) and location and isinstance(location[0], (int, float)):
        return float(location[0])
    if isinstance(location, dict) and isinstance(location.get("x"), (int, float)):
        return float(location["x"])
    x_value = event.get("x")
    if isinstance(x_value, (int, float)):
        return float(x_value)
    return None


def _progression(first_x: float | None, last_x: float | None) -> float:
    if first_x is None or last_x is None:
        return 0.0
    return max(last_x - first_x, 0.0)


def analyze_possession_tempo(
    events: Iterable[dict[str, Any]] | None = None,
    focus_team: str | None = None,
) -> dict[str, Any]:
    event_list = list(events or [])

    possessions: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for index, event in enumerate(event_list):
        team = _team_name(event) or "Unknown Team"
        if focus_team and team != focus_team:
            continue
        possession_id = _possession_id(event, index)
        possessions[(team, possession_id)].append(event)

    team_event_count = sum(len(possession_events) for possession_events in possessions.values())

    possession_rows: list[dict[str, Any]] = []
    team_totals: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "possession_count": 0,
            "total_events": 0,
            "total_duration": 0.0,
            "transition_possessions": 0,
            "total_progression": 0.0,
        }
    )

    for (team, possession_id), possession_events in possessions.items():
        if not possession_events:
            continue

        ordered_events = sorted(
            enumerate(possession_events),
            key=lambda item: (_seconds(item[1]), item[0]),
        )
        ordered = [event for _, event in ordered_events]
        length = len(ordered)
        start_time = _seconds(ordered[0])
        end_time = _seconds(ordered[-1])
        duration = max(end_time - start_time, 0.0)

        first_x = _location_x(ordered[0])
        last_x = _location_x(ordered[-1])
        progression = _progression(first_x, last_x)
        transition = duration <= TRANSITION_DURATION_THRESHOLD and length <= TRANSITION_LENGTH_THRESHOLD

        possession_rows.append(
            {
                "team": team,
                "possession_id": possession_id,
                "length": length,
                "duration": round(duration, 2),
                "progression": round(progression, 2),
                "transition": transition,
                "start_event_type": _event_type(ordered[0]),
                "end_event_type": _event_type(ordered[-1]),
            }
        )

        team_totals[team]["possession_count"] += 1
        team_totals[team]["total_events"] += length
        team_totals[team]["total_duration"] += duration
        team_totals[team]["total_progression"] += progression
        if transition:
            team_totals[team]["transition_possessions"] += 1

    if not possession_rows:
        return {
            "summary": (
                f"No possessions with usable tempo information were available for {focus_team}."
                if focus_team
                else "No possessions with usable tempo information were available."
            ),
            "metrics": {
                "event_count": 0,
                "avg_sequence_length": 0.0,
                "transition_speed": 0.0,
                "avg_possession_duration": 0.0,
                "possession_count": 0,
                "focus_team": focus_team or "",
            },
            "team_breakdown": [],
            "possessions": [],
            "notes": [
                "Tempo requires ordered possessions with timestamps or at least event order.",
                "Once event timing is present, this layer can distinguish patient buildup from direct transitions.",
            ],
        }

    dominant_team = max(
        team_totals.items(),
        key=lambda item: (item[1]["possession_count"], item[1]["total_events"]),
    )[0]
    dominant_totals = team_totals[dominant_team]

    possession_count = int(dominant_totals["possession_count"])
    avg_sequence_length = (
        dominant_totals["total_events"] / possession_count if possession_count else 0.0
    )
    avg_possession_duration = (
        dominant_totals["total_duration"] / possession_count if possession_count else 0.0
    )
    transition_speed = (
        dominant_totals["transition_possessions"] / possession_count if possession_count else 0.0
    )
    progression_rate = dominant_totals["total_progression"] / possession_count if possession_count else 0.0

    team_breakdown = []
    for team, totals in sorted(
        team_totals.items(),
        key=lambda item: (item[1]["possession_count"], item[1]["total_events"]),
        reverse=True,
    ):
        count = int(totals["possession_count"])
        team_breakdown.append(
            {
                "team": team,
                "possession_count": count,
                "avg_sequence_length": round(totals["total_events"] / count if count else 0.0, 2),
                "avg_possession_duration": round(totals["total_duration"] / count if count else 0.0, 2),
                "transition_speed": round(totals["transition_possessions"] / count if count else 0.0, 3),
                "avg_progression": round(totals["total_progression"] / count if count else 0.0, 2),
            }
        )

    possession_rows.sort(
        key=lambda item: (item["transition"], item["duration"], item["length"]),
        reverse=True,
    )

    if avg_sequence_length >= 7 and avg_possession_duration >= 15:
        summary = (
            f"{dominant_team} controlled the tempo with longer possessions averaging "
            f"{avg_sequence_length:.1f} events and {avg_possession_duration:.1f} seconds."
        )
    elif transition_speed >= 0.5:
        summary = (
            f"{dominant_team} played at a quicker tempo, with {transition_speed:.0%} of possessions "
            "classified as transition attacks."
        )
    else:
        summary = (
            f"{dominant_team} showed a mixed tempo profile with {avg_sequence_length:.1f} events per possession."
        )

    return {
        "summary": summary,
        "metrics": {
            "event_count": team_event_count,
            "possession_count": possession_count,
            "avg_sequence_length": round(avg_sequence_length, 2),
            "avg_possession_duration": round(avg_possession_duration, 2),
            "transition_speed": round(transition_speed, 3),
            "progression_rate": round(progression_rate, 2),
            "dominant_team": dominant_team,
            "focus_team": focus_team or dominant_team,
        },
        "team_breakdown": team_breakdown,
        "possessions": possession_rows[:15],
        "notes": [
            "Tempo is derived from possession-level event counts, durations, and progression.",
            "Transition possessions are short and quick, which usually signals direct play or quick counterattacks.",
            "Longer possession durations and higher sequence lengths indicate patience and circulation.",
        ],
    }
