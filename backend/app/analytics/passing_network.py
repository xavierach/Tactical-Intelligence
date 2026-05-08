from __future__ import annotations

from collections import Counter
from collections import defaultdict
from typing import Any, Iterable

import networkx as nx

POSITION_MAP = {
    "Goalkeeper": "GK",
    "Left Back": "LB",
    "Right Back": "RB",
    "Left Wing Back": "LWB",
    "Right Wing Back": "RWB",
    "Left Center Back": "LCB",
    "Right Center Back": "RCB",
    "Center Back": "CB",
    "Left Defensive Midfield": "LDM",
    "Center Defensive Midfield": "CDM",
    "Right Defensive Midfield": "RDM",
    "Left Center Midfield": "LCM",
    "Center Midfield": "CM",
    "Right Center Midfield": "RCM",
    "Left Attacking Midfield": "LAM",
    "Center Attacking Midfield": "CAM",
    "Right Attacking Midfield": "RAM",
    "Left Midfield": "LM",
    "Right Midfield": "RM",
    "Left Wing": "LW",
    "Right Wing": "RW",
    "Center Forward": "ST",
    "Left Center Forward": "LS",
    "Right Center Forward": "RS",
    "Second Striker": "SS",
}

ROLE_COORDINATES = {
    "GK": (8.0, 40.0),
    "LB": (22.0, 18.0),
    "LWB": (25.0, 14.0),
    "LCB": (26.0, 30.0),
    "CB": (25.0, 40.0),
    "RCB": (26.0, 50.0),
    "RB": (22.0, 62.0),
    "LDM": (40.0, 24.0),
    "CDM": (42.0, 40.0),
    "RDM": (40.0, 56.0),
    "LCM": (55.0, 24.0),
    "CM": (56.0, 40.0),
    "RCM": (55.0, 56.0),
    "LAM": (72.0, 20.0),
    "CAM": (74.0, 40.0),
    "RAM": (72.0, 60.0),
    "LM": (62.0, 14.0),
    "RM": (62.0, 66.0),
    "LW": (84.0, 18.0),
    "RW": (84.0, 62.0),
    "ST": (95.0, 40.0),
    "LS": (91.0, 30.0),
    "RS": (91.0, 50.0),
    "SS": (88.0, 40.0),
    "UNK": (50.0, 40.0),
    "SUB": (50.0, 40.0),
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


def _event_type(event: dict[str, Any]) -> str:
    return _string(
        event.get("type")
        or event.get("event_type")
        or event.get("type_name")
        or _value(event, "type", "name")
    ).lower()


def _player_name(event: dict[str, Any]) -> str:
    return _string(event.get("player") or event.get("player_name") or _value(event, "player", "name"))


def _team_name(event: dict[str, Any]) -> str:
    return _string(event.get("team") or event.get("team_name") or _value(event, "team", "name"))


def _is_completed_pass(event: dict[str, Any]) -> bool:
    outcome = event.get("pass_outcome")
    if outcome is None or outcome == "":
        return True
    outcome_name = _string(outcome).lower()
    return outcome_name in {"complete", "successful", "success"}


def _pass_recipient(event: dict[str, Any]) -> str:
    recipient = (
        event.get("pass_recipient")
        or event.get("recipient")
        or _value(event, "pass", "recipient")
        or _value(event, "pass", "recipient", "name")
    )
    return _string(recipient)


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


def _event_player_id(event: dict[str, Any]) -> Any:
    return event.get("player_id") or _value(event, "player", "id")


def _event_team_id(event: dict[str, Any]) -> Any:
    return event.get("team_id") or _value(event, "team", "id")


def _lineup_team_name(record: dict[str, Any]) -> str:
    return _string(
        record.get("team_name")
        or record.get("team")
        or _value(record, "team", "name")
    )


def _position_name(record: dict[str, Any]) -> str:
    position = record.get("position")
    if isinstance(position, dict):
        return _string(position.get("name"))
    if isinstance(position, str):
        return position

    positions = record.get("positions")
    if isinstance(positions, list) and positions:
        first_position = positions[0]
        if isinstance(first_position, dict):
            return _string(first_position.get("position") or first_position.get("name"))
        if isinstance(first_position, str):
            return first_position

    return ""


def _position_abbr(position_name: str) -> str:
    return POSITION_MAP.get(position_name, "UNK")


def _default_coordinates(position_abbr: str) -> tuple[float, float]:
    return ROLE_COORDINATES.get(position_abbr, ROLE_COORDINATES["UNK"])


def _build_position_lookup(
    lineups: Iterable[dict[str, Any]] | None,
    focus_team: str | None,
) -> dict[Any, dict[str, str]]:
    lookup: dict[Any, dict[str, str]] = {}
    if not lineups:
        return lookup

    for record in lineups:
        team_name = _lineup_team_name(record)
        if focus_team and team_name != focus_team:
            continue

        player_name = _string(record.get("player_name") or record.get("player") or record.get("name"))
        player_id = record.get("player_id") or _event_player_id(record)
        position_name = _position_name(record)
        abbr = _position_abbr(position_name)

        if player_name:
            lookup[player_name] = {"abbr": abbr, "position_name": position_name}
        if player_id is not None:
            lookup[player_id] = {"abbr": abbr, "position_name": position_name}

    return lookup


def _player_identifier(event: dict[str, Any]) -> str:
    player_name = _player_name(event)
    if player_name:
        return player_name
    player_id = _event_player_id(event)
    return str(player_id) if player_id is not None else ""


def _infer_recipient(index: int, event_list: list[dict[str, Any]], passer: str, team: str) -> str:
    source_possession = _event_possession(event_list[index])
    for candidate in event_list[index + 1 :]:
        if source_possession is not None and _event_possession(candidate) != source_possession:
            break

        candidate_team = _team_name(candidate)
        if candidate_team and candidate_team != team:
            break

        candidate_player = _player_name(candidate)
        if candidate_player and candidate_player != passer:
            return candidate_player

    return ""


def analyze_passing_network(
    events: Iterable[dict[str, Any]] | None = None,
    focus_team: str | None = None,
    lineups: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    event_list = list(events or [])
    team_events = [
        event for event in event_list if not focus_team or _team_name(event) == focus_team
    ]
    position_lookup = _build_position_lookup(lineups, focus_team)
    player_locations: dict[str, list[tuple[float, float]]] = defaultdict(list)
    player_event_counts: Counter[str] = Counter()

    for event in team_events:
        player_key = _player_identifier(event)
        if not player_key:
            continue

        player_event_counts[player_key] += 1
        location = _location(event)
        if location is not None:
            player_locations[player_key].append(location)

    pass_events = [
        (index, event)
        for index, event in enumerate(event_list)
        if "pass" in _event_type(event)
        and _player_name(event)
        and (not focus_team or _team_name(event) == focus_team)
    ]

    graph = nx.DiGraph()
    node_lookup: dict[str, dict[str, Any]] = {}
    player_stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "completed_passes": 0,
            "passes_received": 0,
            "unique_connections": set(),
            "outgoing_weight": 0,
            "incoming_weight": 0,
        }
    )

    completed_pass_count = 0
    edge_weights: dict[tuple[str, str], int] = defaultdict(int)

    for index, event in pass_events:
        if not _is_completed_pass(event):
            continue

        passer = _player_name(event)
        team = _team_name(event)
        recipient = _pass_recipient(event) or _infer_recipient(index, event_list, passer, team)

        if not passer or not recipient or passer == recipient:
            continue

        completed_pass_count += 1
        edge_weights[(passer, recipient)] += 1

        graph.add_edge(passer, recipient, weight=edge_weights[(passer, recipient)])

        player_stats[passer]["completed_passes"] += 1
        player_stats[passer]["outgoing_weight"] += 1
        player_stats[passer]["unique_connections"].add(recipient)

        player_stats[recipient]["passes_received"] += 1
        player_stats[recipient]["incoming_weight"] += 1
        player_stats[recipient]["unique_connections"].add(passer)

    player_candidates = set(player_event_counts.keys()) | set(position_lookup.keys())

    for player in player_candidates:
        locations = player_locations.get(player, [])
        position_meta = position_lookup.get(player, {})
        position_abbr = position_meta.get("abbr", "UNK")
        position_name = position_meta.get("position_name", "")
        if locations:
            avg_x = round(sum(point[0] for point in locations) / len(locations), 2)
            avg_y = round(sum(point[1] for point in locations) / len(locations), 2)
            has_location = True
        else:
            avg_x, avg_y = _default_coordinates(position_abbr)
            has_location = False

        node_lookup[player] = {
            "name": player,
            "display_name": position_abbr if position_abbr != "UNK" else player,
            "position_abbr": position_abbr,
            "position_name": position_name,
            "x": avg_x,
            "y": avg_y,
            "completed_passes": player_stats[player]["completed_passes"],
            "passes_received": player_stats[player]["passes_received"],
            "outgoing_weight": player_stats[player]["outgoing_weight"],
            "incoming_weight": player_stats[player]["incoming_weight"],
            "unique_connections": len(player_stats[player]["unique_connections"]),
            "weighted_degree": 0.0,
            "betweenness": 0.0,
            "event_count": player_event_counts[player],
            "has_location": has_location,
        }

    if not node_lookup:
        return {
            "summary": (
                f"No completed passing network could be built for {focus_team}."
                if focus_team
                else "No completed passing network could be built from the available events."
            ),
            "metrics": {
                "event_count": len(team_events),
                "pass_event_count": len(pass_events),
                "completed_pass_count": 0,
                "node_count": 0,
                "edge_count": 0,
                "avg_passes_per_player": 0.0,
                "focus_team": focus_team or "",
            },
            "central_players": [],
            "top_connections": [],
            "nodes": [],
            "edges": [],
            "matrix": {},
            "notes": [
                "The network requires completed passes and identifiable passers/recipients.",
                "If this is open data, the next step is to refine recipient inference with pass recipient fields.",
            ],
        }

    selected_players = sorted(
        node_lookup.values(),
        key=lambda item: (item["event_count"], item["has_location"], item["completed_passes"]),
        reverse=True,
    )[:11]
    selected_player_names = {item["name"] for item in selected_players}

    graph.add_nodes_from(selected_player_names)
    weighted_degree = dict(graph.degree(weight="weight"))
    out_degree = dict(graph.out_degree(weight="weight"))
    in_degree = dict(graph.in_degree(weight="weight"))
    betweenness = (
        nx.betweenness_centrality(graph, weight="weight", normalized=True)
        if graph.number_of_nodes() > 1
        else {}
    )

    centrality_scores: list[tuple[str, float]] = []
    for player in selected_player_names:
        score = (
            weighted_degree.get(player, 0.0)
            + out_degree.get(player, 0.0)
            + in_degree.get(player, 0.0)
            + (betweenness.get(player, 0.0) * 10.0)
        )
        centrality_scores.append((player, score))

    central_players = [player for player, _ in sorted(centrality_scores, key=lambda item: item[1], reverse=True)[:5]]

    nodes: list[dict[str, Any]] = []
    for player in selected_players:
        name = player["name"]
        unique_connections = player_stats[name]["unique_connections"]
        nodes.append(
            {
                "name": name,
                "display_name": player["display_name"],
                "position_abbr": player["position_abbr"],
                "position_name": player["position_name"],
                "x": player["x"],
                "y": player["y"],
                "completed_passes": player_stats[name]["completed_passes"],
                "passes_received": player_stats[name]["passes_received"],
                "outgoing_weight": player_stats[name]["outgoing_weight"],
                "incoming_weight": player_stats[name]["incoming_weight"],
                "unique_connections": len(unique_connections),
                "weighted_degree": round(weighted_degree.get(name, 0.0), 3),
                "betweenness": round(betweenness.get(name, 0.0), 3),
                "event_count": player["event_count"],
                "has_location": player["has_location"],
            }
        )

    nodes.sort(key=lambda item: (item["weighted_degree"], item["completed_passes"], item["unique_connections"]), reverse=True)

    edges = [
        {
            "source": source,
            "target": target,
            "weight": weight,
        }
        for (source, target), weight in sorted(edge_weights.items(), key=lambda item: item[1], reverse=True)
        if source in selected_player_names and target in selected_player_names
    ]

    matrix: dict[str, dict[str, int]] = {}
    for source, target in graph.edges:
        if source not in selected_player_names or target not in selected_player_names:
            continue
        matrix.setdefault(source, {})
        matrix[source][target] = edge_weights[(source, target)]

    avg_passes_per_player = completed_pass_count / max(graph.number_of_nodes(), 1)
    top_connections = edges[:5]

    if central_players:
        summary = (
            f"Passing network for {focus_team or 'the selected team'} built from {completed_pass_count} completed passes "
            f"across {len(nodes)} players, led by {central_players[0]}."
        )
    else:
        summary = (
            f"Passing network for {focus_team or 'the selected team'} built from {completed_pass_count} completed passes "
            f"across {len(nodes)} players."
        )

    return {
        "summary": summary,
        "metrics": {
            "event_count": len(team_events),
            "pass_event_count": len(pass_events),
            "completed_pass_count": completed_pass_count,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "avg_passes_per_player": round(completed_pass_count / max(len(nodes), 1), 2),
            "focus_team": focus_team or "",
        },
        "central_players": central_players,
        "top_connections": top_connections,
        "nodes": nodes,
        "edges": edges,
        "matrix": matrix,
        "notes": [
            "Completed passes are connected to the next identifiable teammate when a recipient is not explicitly provided.",
            "Use the top connections and central players to describe buildup hubs and circulation patterns.",
        ],
    }
