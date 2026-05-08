from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def _format_number(value: Any) -> str:
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _join_players(players: list[str]) -> str:
    if not players:
        return "no clear central players"
    if len(players) == 1:
        return players[0]
    if len(players) == 2:
        return f"{players[0]} and {players[1]}"
    return f"{', '.join(players[:-1])}, and {players[-1]}"


@dataclass(slots=True)
class MatchSummary:
    match: dict[str, Any]
    attacking: dict[str, Any]
    defensive: dict[str, Any]
    players: dict[str, Any]
    tempo: dict[str, Any]
    themes: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    confidence: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _attacking_summary(analytics: dict[str, Any]) -> tuple[dict[str, Any], list[str], str]:
    passing = analytics.get("passing_network", {})
    metrics = passing.get("metrics", {})
    central_players = passing.get("central_players", []) or []
    top_connections = passing.get("top_connections", [])[:3]
    if central_players:
        headline = f"Build-up flowed through {_join_players(central_players[:3])}."
    else:
        headline = "The passing network did not reveal a clear hub."

    evidence = [
        f"Completed passes: {_format_number(metrics.get('completed_pass_count', 0))}",
        f"Nodes: {_format_number(metrics.get('node_count', 0))}",
        f"Edges: {_format_number(metrics.get('edge_count', 0))}",
        f"Average passes per player: {_format_number(metrics.get('avg_passes_per_player', 0.0))}",
        f"Central players: {_join_players(central_players[:3])}",
    ]
    if top_connections:
        evidence.append(
            "Top connections: "
            + "; ".join(
                f"{item['source']} -> {item['target']} ({item['weight']})" for item in top_connections
            )
        )

    payload = {
        "headline": headline,
        "metrics": {
            "event_count": metrics.get("event_count", 0),
            "completed_pass_count": metrics.get("completed_pass_count", 0),
            "node_count": metrics.get("node_count", 0),
            "edge_count": metrics.get("edge_count", 0),
            "avg_passes_per_player": metrics.get("avg_passes_per_player", 0.0),
        },
        "central_players": central_players[:5],
        "top_connections": top_connections,
        "summary": passing.get("summary", ""),
    }
    return payload, evidence, headline


def _defensive_summary(analytics: dict[str, Any]) -> tuple[dict[str, Any], list[str], str]:
    defensive = analytics.get("defensive_spacing", {})
    metrics = defensive.get("metrics", {})
    compactness = float(metrics.get("compactness", 0.0) or 0.0)
    line_stretch = float(metrics.get("line_stretch", 0.0) or 0.0)
    dominant_team = defensive.get("team_breakdown", [{}])[0].get("team", "Unknown Team")
    if compactness >= 0.7:
        headline = f"{dominant_team} stayed compact and difficult to play through."
    elif line_stretch >= 0.5:
        headline = f"{dominant_team} looked stretched between the lines."
    else:
        headline = f"{dominant_team} showed a mixed defensive spacing profile."

    evidence = [
        f"Defensive actions: {_format_number(metrics.get('defensive_action_count', 0))}",
        f"Compactness: {_format_number(compactness)}",
        f"Line stretch: {_format_number(line_stretch)}",
        f"Centroid: ({_format_number(metrics.get('centroid_x', 0.0))}, {_format_number(metrics.get('centroid_y', 0.0))})",
    ]

    payload = {
        "headline": headline,
        "metrics": {
            "event_count": metrics.get("event_count", 0),
            "defensive_action_count": metrics.get("defensive_action_count", 0),
            "dominant_team_defensive_count": metrics.get("dominant_team_defensive_count", 0),
            "compactness": compactness,
            "line_stretch": line_stretch,
            "centroid_x": metrics.get("centroid_x", 0.0),
            "centroid_y": metrics.get("centroid_y", 0.0),
        },
        "dominant_team": dominant_team,
        "team_breakdown": defensive.get("team_breakdown", []),
        "gaps": defensive.get("gaps", []),
        "summary": defensive.get("summary", ""),
    }
    return payload, evidence, headline


def _players_summary(analytics: dict[str, Any]) -> tuple[dict[str, Any], list[str], str]:
    player = analytics.get("player_impact", {})
    metrics = player.get("metrics", {})
    players = player.get("players", [])[:5]
    top_player = players[0] if players else {}
    top_name = top_player.get("name") if isinstance(top_player, dict) else ""
    if top_name:
        headline = f"{top_name} produced the strongest individual impact."
    else:
        headline = "No single player clearly dominated the summary."

    evidence = [
        f"Total xG contribution: {_format_number(metrics.get('xg_contribution', 0.0))}",
        f"Key passes: {_format_number(metrics.get('key_passes', 0))}",
        f"Shots: {_format_number(metrics.get('shot_count', 0))}",
        f"Player count: {_format_number(metrics.get('player_count', 0))}",
    ]
    if top_player:
        evidence.append(
            "Top player line: "
            + ", ".join(
                [
                    f"{top_player.get('name', '')}",
                    f"team {top_player.get('team', '')}",
                    f"xG {_format_number(top_player.get('xg', 0.0))}",
                    f"key passes {_format_number(top_player.get('key_passes', 0))}",
                    f"shots {_format_number(top_player.get('shots', 0))}",
                ]
            )
        )

    payload = {
        "headline": headline,
        "metrics": {
            "event_count": metrics.get("event_count", 0),
            "xg_contribution": metrics.get("xg_contribution", 0.0),
            "key_passes": metrics.get("key_passes", 0),
            "shot_count": metrics.get("shot_count", 0),
            "assist_count": metrics.get("assist_count", 0),
            "player_count": metrics.get("player_count", 0),
            "possession_share": metrics.get("possession_share", 0.0),
        },
        "top_player": top_player,
        "players": players,
        "summary": player.get("summary", ""),
    }
    return payload, evidence, headline


def _tempo_summary(analytics: dict[str, Any]) -> tuple[dict[str, Any], list[str], str]:
    tempo = analytics.get("tempo", {})
    metrics = tempo.get("metrics", {})
    avg_sequence_length = float(metrics.get("avg_sequence_length", 0.0) or 0.0)
    transition_speed = float(metrics.get("transition_speed", 0.0) or 0.0)
    dominant_team = metrics.get("dominant_team", "Unknown Team")
    if avg_sequence_length >= 7 and metrics.get("avg_possession_duration", 0.0) >= 15:
        headline = f"{dominant_team} controlled tempo with longer possessions."
    elif transition_speed >= 0.5:
        headline = f"{dominant_team} attacked quickly in transition."
    else:
        headline = f"{dominant_team} showed a mixed tempo profile."

    evidence = [
        f"Possessions: {_format_number(metrics.get('possession_count', 0))}",
        f"Average sequence length: {_format_number(avg_sequence_length)}",
        f"Average possession duration: {_format_number(metrics.get('avg_possession_duration', 0.0))}",
        f"Transition speed: {_format_number(transition_speed)}",
        f"Progression rate: {_format_number(metrics.get('progression_rate', 0.0))}",
    ]

    payload = {
        "headline": headline,
        "metrics": {
            "event_count": metrics.get("event_count", 0),
            "possession_count": metrics.get("possession_count", 0),
            "avg_sequence_length": avg_sequence_length,
            "avg_possession_duration": metrics.get("avg_possession_duration", 0.0),
            "transition_speed": transition_speed,
            "progression_rate": metrics.get("progression_rate", 0.0),
        },
        "dominant_team": dominant_team,
        "team_breakdown": tempo.get("team_breakdown", []),
        "possessions": tempo.get("possessions", [])[:5],
        "summary": tempo.get("summary", ""),
    }
    return payload, evidence, headline


def build_match_summary(match: dict[str, Any], analytics: dict[str, Any]) -> MatchSummary:
    attacking, attacking_evidence, attacking_headline = _attacking_summary(analytics)
    defensive, defensive_evidence, defensive_headline = _defensive_summary(analytics)
    players, players_evidence, players_headline = _players_summary(analytics)
    tempo, tempo_evidence, tempo_headline = _tempo_summary(analytics)

    themes = [
        attacking_headline,
        defensive_headline,
        players_headline,
        tempo_headline,
    ]

    evidence = [
        *attacking_evidence,
        *defensive_evidence,
        *players_evidence,
        *tempo_evidence,
    ]

    confidence_buckets = [
        analytics.get("passing_network", {}).get("metrics", {}).get("event_count", 0),
        analytics.get("defensive_spacing", {}).get("metrics", {}).get("event_count", 0),
        analytics.get("player_impact", {}).get("metrics", {}).get("event_count", 0),
        analytics.get("tempo", {}).get("metrics", {}).get("event_count", 0),
    ]
    if all(count > 0 for count in confidence_buckets):
        confidence = "high"
    elif sum(count > 0 for count in confidence_buckets) >= 2:
        confidence = "medium"
    else:
        confidence = "low"

    return MatchSummary(
        match={
            "match_id": match.get("match_id"),
            "competition": match.get("competition"),
            "season": match.get("season"),
            "home_team": match.get("home_team"),
            "away_team": match.get("away_team"),
            "focus_team": match.get("focus_team") or match.get("home_team"),
            "kickoff": match.get("kickoff"),
            "venue": match.get("venue"),
        },
        attacking=attacking,
        defensive=defensive,
        players=players,
        tempo=tempo,
        themes=themes,
        evidence=evidence,
        confidence=confidence,
    )
