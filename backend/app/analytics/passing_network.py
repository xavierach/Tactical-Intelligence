from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

import networkx as nx


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


def analyze_passing_network(events: Iterable[dict[str, Any]] | None = None) -> dict[str, Any]:
    event_list = list(events or [])

    pass_events = [
        (index, event)
        for index, event in enumerate(event_list)
        if "pass" in _event_type(event) and _player_name(event)
    ]

    graph = nx.DiGraph()
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

    if graph.number_of_nodes() == 0:
        return {
            "summary": "No completed passing network could be built from the available events.",
            "metrics": {
                "event_count": len(event_list),
                "pass_event_count": len(pass_events),
                "completed_pass_count": 0,
                "node_count": 0,
                "edge_count": 0,
                "avg_passes_per_player": 0.0,
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

    weighted_degree = dict(graph.degree(weight="weight"))
    out_degree = dict(graph.out_degree(weight="weight"))
    in_degree = dict(graph.in_degree(weight="weight"))
    betweenness = nx.betweenness_centrality(graph, weight="weight", normalized=True)

    centrality_scores: list[tuple[str, float]] = []
    for player in graph.nodes:
        score = (
            weighted_degree.get(player, 0.0)
            + out_degree.get(player, 0.0)
            + in_degree.get(player, 0.0)
            + (betweenness.get(player, 0.0) * 10.0)
        )
        centrality_scores.append((player, score))

    central_players = [player for player, _ in sorted(centrality_scores, key=lambda item: item[1], reverse=True)[:5]]

    nodes: list[dict[str, Any]] = []
    for player in graph.nodes:
        unique_connections = player_stats[player]["unique_connections"]
        nodes.append(
            {
                "name": player,
                "completed_passes": player_stats[player]["completed_passes"],
                "passes_received": player_stats[player]["passes_received"],
                "outgoing_weight": player_stats[player]["outgoing_weight"],
                "incoming_weight": player_stats[player]["incoming_weight"],
                "unique_connections": len(unique_connections),
                "weighted_degree": round(weighted_degree.get(player, 0.0), 3),
                "betweenness": round(betweenness.get(player, 0.0), 3),
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
    ]

    matrix: dict[str, dict[str, int]] = {}
    for source, target in graph.edges:
        matrix.setdefault(source, {})
        matrix[source][target] = edge_weights[(source, target)]

    avg_passes_per_player = completed_pass_count / max(graph.number_of_nodes(), 1)
    top_connections = edges[:5]

    if central_players:
        summary = (
            f"Passing network built from {completed_pass_count} completed passes across "
            f"{graph.number_of_nodes()} players, led by {central_players[0]}."
        )
    else:
        summary = (
            f"Passing network built from {completed_pass_count} completed passes across "
            f"{graph.number_of_nodes()} players."
        )

    return {
        "summary": summary,
        "metrics": {
            "event_count": len(event_list),
            "pass_event_count": len(pass_events),
            "completed_pass_count": completed_pass_count,
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "avg_passes_per_player": round(avg_passes_per_player, 2),
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
