from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable


ROUTE_LABELS = {
    "left_wing": "Left wing",
    "left_half_space": "Left half-space",
    "center": "Central lane",
    "right_half_space": "Right half-space",
    "right_wing": "Right wing",
    "direct_launch": "Direct launch",
}


def _value(value: Any, *keys: str) -> Any:
    current = value
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return current
    return current


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
    return _string(event.get("team") or event.get("team_name") or _value(event, "team", "name"))


def _player_name(event: dict[str, Any]) -> str:
    return _string(event.get("player") or event.get("player_name") or _value(event, "player", "name"))


def _event_type(event: dict[str, Any]) -> str:
    return _string(
        event.get("type")
        or event.get("event_type")
        or event.get("type_name")
        or _value(event, "type", "name")
    ).lower()


def _event_possession(event: dict[str, Any]) -> Any:
    return event.get("possession") or event.get("possession_id")


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


def _pass_height(pass_event: dict[str, Any]) -> str:
    height = pass_event.get("height")
    if isinstance(height, dict):
        return _string(height.get("name")).lower()
    return _string(height).lower()


def _pass_outcome(pass_event: dict[str, Any]) -> str:
    outcome = pass_event.get("outcome")
    if isinstance(outcome, dict):
        return _string(outcome.get("name")).lower()
    return _string(outcome).lower()


def _lane_from_y(y: float) -> str:
    if y < 16:
        return "left_wing"
    if y < 32:
        return "left_half_space"
    if y < 48:
        return "center"
    if y < 64:
        return "right_half_space"
    return "right_wing"


def _route_label(route_key: str) -> str:
    return ROUTE_LABELS.get(route_key, route_key.replace("_", " ").title())


def analyze_attacking_routes(
    events: Iterable[dict[str, Any]] | None = None,
    focus_team: str | None = None,
    lineups: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    event_list = list(events or [])
    team_events = [event for event in event_list if not focus_team or _team_name(event) == focus_team]

    possession_events: dict[Any, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
    for index, event in enumerate(team_events):
        possession = _event_possession(event)
        if possession is None:
            continue
        possession_events[possession].append((index, event))

    route_buckets: dict[str, dict[str, Any]] = {}
    total_box_entries = 0
    total_final_third_entries = 0
    total_long_passes = 0
    total_progressive_passes = 0

    for possession_id, indexed_events in possession_events.items():
        ordered_events = [event for _, event in sorted(indexed_events, key=lambda item: item[0])]
        locations = [loc for event in ordered_events if (loc := _location(event)) is not None]
        if not locations:
            continue

        sequence_length = len(ordered_events)
        start_x, start_y = locations[0]
        end_x, end_y = locations[-1]
        avg_y = sum(y for _, y in locations) / len(locations)

        pass_count = 0
        completed_pass_count = 0
        long_pass_count = 0
        progressive_pass_count = 0
        shot_count = 0
        xg_total = 0.0
        box_entry = False
        final_third_entry = False
        passers: Counter[str] = Counter()
        receivers: Counter[str] = Counter()

        for event in ordered_events:
            location = _location(event)
            if location:
                x, y = location
                if x >= 80:
                    final_third_entry = True
                if x >= 102 and 18 <= y <= 62:
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
            if _pass_outcome(pass_info) in {"", "complete", "successful", "success"}:
                completed_pass_count += 1

            start_location = location
            end_location = _end_location(pass_info)
            length = _pass_length(pass_info, start_location, end_location)
            if length >= 30 or "high pass" in _pass_height(pass_info) or "cross" in _pass_height(pass_info):
                long_pass_count += 1
            if start_location and end_location and end_location[0] - start_location[0] >= 15:
                progressive_pass_count += 1

            passer = _player_name(event)
            recipient = _string(
                pass_info.get("recipient")
                or pass_info.get("pass_recipient")
                or pass_info.get("recipient_name")
            )
            if passer:
                passers[passer] += 1
            if recipient:
                receivers[recipient] += 1

        total_long_passes += long_pass_count
        total_progressive_passes += progressive_pass_count
        total_box_entries += int(box_entry)
        total_final_third_entries += int(final_third_entry)

        direct_launch = long_pass_count > 0 and (sequence_length <= 5 or final_third_entry or progressive_pass_count >= 1)
        route_key = "direct_launch" if direct_launch else _lane_from_y(avg_y)
        bucket = route_buckets.setdefault(
            route_key,
            {
                "key": route_key,
                "label": _route_label(route_key),
                "possessions": 0,
                "shots": 0,
                "xg": 0.0,
                "box_entries": 0,
                "final_third_entries": 0,
                "sequence_length_total": 0,
                "completed_passes": 0,
                "pass_attempts": 0,
                "long_passes": 0,
                "progressive_passes": 0,
                "passers": Counter(),
                "receivers": Counter(),
                "scores": [],
                "sample_possessions": [],
            },
        )

        bucket["possessions"] += 1
        bucket["shots"] += shot_count
        bucket["xg"] += xg_total
        bucket["box_entries"] += int(box_entry)
        bucket["final_third_entries"] += int(final_third_entry)
        bucket["sequence_length_total"] += sequence_length
        bucket["completed_passes"] += completed_pass_count
        bucket["pass_attempts"] += pass_count
        bucket["long_passes"] += long_pass_count
        bucket["progressive_passes"] += progressive_pass_count
        bucket["passers"].update(passers)
        bucket["receivers"].update(receivers)
        bucket["sample_possessions"].append(
            {
                "possession_id": possession_id,
                "sequence_length": sequence_length,
                "start": {"x": start_x, "y": start_y},
                "end": {"x": end_x, "y": end_y},
                "direct_launch": direct_launch,
                "box_entry": box_entry,
                "final_third_entry": final_third_entry,
                "shot_count": shot_count,
                "xg": round(xg_total, 3),
            }
        )
        bucket["scores"].append(
            (
                xg_total * 10.0
                + shot_count * 4.0
                + int(box_entry) * 3.0
                + int(final_third_entry) * 1.5
                + max(end_x - start_x, 0.0) * 0.04
            )
            / max(sequence_length, 1)
        )

    routes: list[dict[str, Any]] = []
    for route_key, bucket in route_buckets.items():
        possessions = bucket["possessions"]
        completion_rate = bucket["completed_passes"] / bucket["pass_attempts"] if bucket["pass_attempts"] else 0.0
        avg_sequence_length = bucket["sequence_length_total"] / possessions if possessions else 0.0
        xg_per_possession = bucket["xg"] / possessions if possessions else 0.0
        route_players = sorted(bucket["passers"].items(), key=lambda item: item[1], reverse=True)
        route_receivers = sorted(bucket["receivers"].items(), key=lambda item: item[1], reverse=True)
        route_score = sum(bucket["scores"]) / len(bucket["scores"]) if bucket["scores"] else 0.0
        routes.append(
            {
                "key": route_key,
                "label": bucket["label"],
                "possessions": possessions,
                "share": possessions / max(len(possession_events), 1),
                "shots": bucket["shots"],
                "xg": round(bucket["xg"], 3),
                "xg_per_possession": round(xg_per_possession, 3),
                "box_entries": bucket["box_entries"],
                "final_third_entries": bucket["final_third_entries"],
                "avg_sequence_length": round(avg_sequence_length, 2),
                "pass_completion_rate": round(completion_rate, 3),
                "long_passes": bucket["long_passes"],
                "progressive_passes": bucket["progressive_passes"],
                "top_passers": [{"name": name, "count": count} for name, count in route_players[:3]],
                "top_receivers": [{"name": name, "count": count} for name, count in route_receivers[:3]],
                "sample_possessions": bucket["sample_possessions"][:3],
                "score": round(route_score, 3),
                "summary": (
                    f"{bucket['label']}: {possessions} possessions, {bucket['box_entries']} box entries, "
                    f"{bucket['shots']} shots, {bucket['xg']:.2f} xG."
                ),
            }
        )

    routes.sort(key=lambda item: (item["score"], item["xg_per_possession"], item["box_entries"]), reverse=True)
    best_route = routes[0] if routes else {}
    runner_up_route = routes[1] if len(routes) > 1 else {}

    if best_route:
        headline = (
            "Direct launches produced the clearest attacking returns."
            if best_route["key"] == "direct_launch"
            else f"{best_route['label']} attacks produced the strongest returns."
        )
    else:
        headline = "The attack did not produce a clear route preference."

    route_evidence: list[str] = []
    if best_route:
        route_evidence.append(
            f"Best route: {best_route['label']} with {best_route['possessions']} possessions, "
            f"{best_route['box_entries']} box entries, {best_route['shots']} shots, {best_route['xg']:.2f} xG."
        )
        if best_route.get("top_passers"):
            top_passers = ", ".join(player["name"] for player in best_route["top_passers"])
            route_evidence.append(f"Top passers on the best route: {top_passers}")
        if best_route.get("top_receivers"):
            top_receivers = ", ".join(player["name"] for player in best_route["top_receivers"])
            route_evidence.append(f"Top receivers on the best route: {top_receivers}")
    if runner_up_route:
        route_evidence.append(
            f"Runner-up: {runner_up_route['label']} with {runner_up_route['possessions']} possessions and "
            f"{runner_up_route['xg']:.2f} xG."
        )

    summary = (
        f"{headline} The team generated {total_box_entries} box entries and "
        f"{total_final_third_entries} final-third entries across {len(possession_events)} possessions."
    )

    return {
        "headline": headline,
        "metrics": {
            "event_count": len(team_events),
            "possession_count": len(possession_events),
            "route_count": len(routes),
            "box_entries": total_box_entries,
            "final_third_entries": total_final_third_entries,
            "long_passes": total_long_passes,
            "progressive_passes": total_progressive_passes,
        },
        "routes": routes,
        "best_route": best_route,
        "runner_up_route": runner_up_route,
        "route_evidence": route_evidence,
        "summary": summary,
    }
