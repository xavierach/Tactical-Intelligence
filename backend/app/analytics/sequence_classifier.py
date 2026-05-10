from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Iterable


SEQUENCE_LABELS = {
    "buildup": "Buildup",
    "direct_attack": "Direct attack",
    "counterattack": "Counterattack",
    "switch_play": "Switch of play",
    "wide_progression": "Wide progression",
    "central_progression": "Central progression",
    "chance_attack": "Chance creation",
}

SEQUENCE_ORDER = [
    "chance_attack",
    "counterattack",
    "direct_attack",
    "switch_play",
    "wide_progression",
    "central_progression",
    "buildup",
]

THIRD_START = 80.0
BOX_START = 102.0
BOX_Y_MIN = 18.0
BOX_Y_MAX = 62.0


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


def _team_name(event: dict[str, Any]) -> str:
    return _string(event.get("team") or event.get("team_name"))


def _event_type(event: dict[str, Any]) -> str:
    return _string(
        event.get("type")
        or event.get("event_type")
        or event.get("type_name")
        or event.get("sub_type")
    ).lower()


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


def _pass_event(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("pass")
    return value if isinstance(value, dict) else {}


def _shot_event(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("shot")
    return value if isinstance(value, dict) else {}


def _end_location(pass_event: dict[str, Any]) -> tuple[float, float] | None:
    end_location = pass_event.get("end_location") or pass_event.get("endLocation")
    if isinstance(end_location, dict):
        x = end_location.get("x")
        y = end_location.get("y")
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            return float(x), float(y)
    elif isinstance(end_location, (list, tuple)) and len(end_location) >= 2:
        x, y = end_location[0], end_location[1]
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            return float(x), float(y)
    return None


def _pass_length(pass_event: dict[str, Any], start: tuple[float, float] | None, end: tuple[float, float] | None) -> float:
    value = pass_event.get("length")
    if isinstance(value, (int, float)):
        return float(value)
    if start and end:
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        return (dx * dx + dy * dy) ** 0.5
    return 0.0


def _classify_sequence(
    ordered_events: list[dict[str, Any]],
    start_location: tuple[float, float] | None,
    end_location: tuple[float, float] | None,
    pass_count: int,
    completed_pass_count: int,
    long_pass_count: int,
    progressive_pass_count: int,
    shot_count: int,
    xg_total: float,
) -> str:
    sequence_length = len(ordered_events)
    duration = max(_seconds(ordered_events[-1]) - _seconds(ordered_events[0]), 0.0) if ordered_events else 0.0
    start_x, start_y = start_location or (0.0, 0.0)
    end_x, end_y = end_location or (0.0, 0.0)
    lateral_shift = abs(end_y - start_y)
    progression = max(end_x - start_x, 0.0)

    if shot_count > 0 or xg_total > 0.05 or end_x >= BOX_START:
        return "chance_attack"
    if long_pass_count > 0 and (sequence_length <= 5 or progression >= 20):
        return "direct_attack"
    if duration <= 8.0 and sequence_length <= 5 and progression >= 18:
        return "counterattack"
    if lateral_shift >= 20.0 and progression < 20.0 and pass_count >= 3:
        return "switch_play"
    if (start_y <= 20.0 or start_y >= 60.0 or end_y <= 20.0 or end_y >= 60.0) and progression >= 10.0:
        return "wide_progression"
    if progression >= 18.0 and progressive_pass_count >= 1 and pass_count >= 3:
        return "central_progression"
    if sequence_length >= 8 or duration >= 15.0:
        return "buildup"
    if completed_pass_count >= 2 and pass_count <= 3:
        return "direct_attack"
    return "buildup"


def analyze_possession_sequences(
    events: Iterable[dict[str, Any]] | None = None,
    focus_team: str | None = None,
) -> dict[str, Any]:
    event_list = list(events or [])
    team_events = [
        event for event in event_list if not focus_team or _team_name(event) == focus_team
    ]

    possessions: dict[int, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for index, event in enumerate(team_events):
        possession_id = _possession_id(event, index)
        possessions[possession_id].append((index, event))

    sequence_rows: list[dict[str, Any]] = []
    sequence_totals: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "count": 0,
            "events": 0,
            "duration": 0.0,
            "progression": 0.0,
            "shots": 0,
            "xg": 0.0,
            "box_entries": 0,
            "final_third_entries": 0,
        }
    )

    for possession_id, indexed_events in possessions.items():
        ordered_events = [event for _, event in sorted(indexed_events, key=lambda item: (_seconds(item[1]), item[0]))]
        if not ordered_events:
            continue

        locations = [loc for event in ordered_events if (loc := _location(event)) is not None]
        start_location = locations[0] if locations else None
        end_location = locations[-1] if locations else None
        sequence_length = len(ordered_events)
        duration = max(_seconds(ordered_events[-1]) - _seconds(ordered_events[0]), 0.0)
        progression = 0.0
        lateral_shift = 0.0
        if start_location and end_location:
            progression = max(end_location[0] - start_location[0], 0.0)
            lateral_shift = abs(end_location[1] - start_location[1])

        pass_count = 0
        completed_pass_count = 0
        long_pass_count = 0
        progressive_pass_count = 0
        shot_count = 0
        xg_total = 0.0
        box_entry = False
        final_third_entry = False

        for event in ordered_events:
            event_location = _location(event)
            if event_location:
                x, y = event_location
                if x >= THIRD_START:
                    final_third_entry = True
                if x >= BOX_START and BOX_Y_MIN <= y <= BOX_Y_MAX:
                    box_entry = True

            event_type = _event_type(event)
            if event_type == "shot":
                shot_count += 1
                shot = _shot_event(event)
                xg = shot.get("statsbomb_xg")
                if isinstance(xg, (int, float)):
                    xg_total += float(xg)
                continue
            if event_type != "pass":
                continue

            pass_info = _pass_event(event)
            pass_count += 1
            outcome = _string(pass_info.get("outcome")).lower()
            if outcome in {"", "complete", "successful", "success"}:
                completed_pass_count += 1

            start = event_location
            end = _end_location(pass_info)
            length = _pass_length(pass_info, start, end)
            if length >= 30 or "high pass" in _string(pass_info.get("height")).lower() or "cross" in _string(pass_info.get("height")).lower():
                long_pass_count += 1
            if start and end and end[0] - start[0] >= 15:
                progressive_pass_count += 1

        sequence_type = _classify_sequence(
            ordered_events,
            start_location,
            end_location,
            pass_count,
            completed_pass_count,
            long_pass_count,
            progressive_pass_count,
            shot_count,
            xg_total,
        )

        sequence_rows.append(
            {
                "possession_id": possession_id,
                "team": focus_team or _team_name(ordered_events[0]) or "Unknown Team",
                "sequence_type": sequence_type,
                "sequence_label": SEQUENCE_LABELS.get(sequence_type, sequence_type.replace("_", " ").title()),
                "length": sequence_length,
                "duration": round(duration, 2),
                "progression": round(progression, 2),
                "lateral_shift": round(lateral_shift, 2),
                "pass_count": pass_count,
                "completed_pass_count": completed_pass_count,
                "long_pass_count": long_pass_count,
                "progressive_pass_count": progressive_pass_count,
                "shot_count": shot_count,
                "xg": round(xg_total, 3),
                "box_entry": box_entry,
                "final_third_entry": final_third_entry,
                "start_event_type": _event_type(ordered_events[0]),
                "end_event_type": _event_type(ordered_events[-1]),
            }
        )

        totals = sequence_totals[sequence_type]
        totals["count"] += 1
        totals["events"] += sequence_length
        totals["duration"] += duration
        totals["progression"] += progression
        totals["shots"] += shot_count
        totals["xg"] += xg_total
        totals["box_entries"] += int(box_entry)
        totals["final_third_entries"] += int(final_third_entry)

    if not sequence_rows:
        return {
            "summary": (
                f"No possession sequences with usable timing information were available for {focus_team}."
                if focus_team
                else "No possession sequences with usable timing information were available."
            ),
            "metrics": {
                "event_count": 0,
                "possession_count": 0,
                "sequence_count": 0,
                "focus_team": focus_team or "",
            },
            "sequence_breakdown": [],
            "sequence_examples": [],
            "best_sequence": {},
            "notes": [
                "Sequence classification needs ordered possessions with locations or timestamps.",
                "Once event timing and location are available, the classifier can separate buildup from direct attacks.",
            ],
        }

    sequence_rows.sort(
        key=lambda item: (
            item["xg"],
            item["box_entry"],
            item["final_third_entry"],
            item["progression"],
            item["shot_count"],
        ),
        reverse=True,
    )

    breakdown: list[dict[str, Any]] = []
    for sequence_type in SEQUENCE_ORDER:
        totals = sequence_totals.get(sequence_type)
        if not totals:
            continue
        count = int(totals["count"])
        breakdown.append(
            {
                "sequence_type": sequence_type,
                "sequence_label": SEQUENCE_LABELS.get(sequence_type, sequence_type.replace("_", " ").title()),
                "count": count,
                "share": round(count / len(sequence_rows), 3),
                "avg_length": round(totals["events"] / count if count else 0.0, 2),
                "avg_duration": round(totals["duration"] / count if count else 0.0, 2),
                "avg_progression": round(totals["progression"] / count if count else 0.0, 2),
                "shots": int(totals["shots"]),
                "xg": round(totals["xg"], 3),
                "box_entries": int(totals["box_entries"]),
                "final_third_entries": int(totals["final_third_entries"]),
            }
        )

    best_sequence = sequence_rows[0]
    runner_up_sequence = sequence_rows[1] if len(sequence_rows) > 1 else {}

    if best_sequence["sequence_type"] == "direct_attack":
        headline = "Direct attacks produced the clearest returns."
    elif best_sequence["sequence_type"] == "counterattack":
        headline = "Counterattacks were the most efficient sequence type."
    elif best_sequence["sequence_type"] == "switch_play":
        headline = "Switches of play created the strongest attacking outcomes."
    elif best_sequence["sequence_type"] == "wide_progression":
        headline = "Wide progression delivered the most effective entries."
    elif best_sequence["sequence_type"] == "central_progression":
        headline = "Central progression produced the strongest returns."
    elif best_sequence["sequence_type"] == "chance_attack":
        headline = "Final-third attacks produced the clearest danger."
    else:
        headline = "Buildup sequences dominated the attacking picture."

    evidence = [
        f"Best sequence: {best_sequence['sequence_label']} with {best_sequence['xg']:.2f} xG, "
        f"{'1' if best_sequence['box_entry'] else '0'} box entries, "
        f"{best_sequence['shot_count']} shots."
    ]
    if runner_up_sequence:
        evidence.append(
            f"Runner-up: {runner_up_sequence['sequence_label']} with {runner_up_sequence['xg']:.2f} xG."
        )

    summary = (
        f"{headline} The team generated {len(sequence_rows)} analysable possession sequences, "
        f"with {best_sequence['sequence_label'].lower()} as the most productive type."
    )

    return {
        "summary": summary,
        "headline": headline,
        "metrics": {
            "event_count": len(team_events),
            "possession_count": len(possessions),
            "sequence_count": len(sequence_rows),
            "focus_team": focus_team or "",
        },
        "sequence_breakdown": breakdown,
        "sequence_examples": sequence_rows[:10],
        "best_sequence": best_sequence,
        "runner_up_sequence": runner_up_sequence,
        "notes": [
            "Sequence types are derived from possession duration, progression, verticality, lateral shift, shots, and xG.",
            "Direct attacks and counterattacks are identified by short, fast possessions with strong progression.",
            "Wide and central progression are identified by the final attacking lane and whether the move switches sides.",
        ],
    }
