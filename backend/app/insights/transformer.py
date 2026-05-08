from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ActionableInsight:
    section: str
    headline: str
    evidence: list[str] = field(default_factory=list)
    implication: str = ""
    recommendation: str = ""
    confidence: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _format_number(value: Any) -> str:
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return f"{value}"
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


def _as_metric_block(title: str, metrics: dict[str, Any], focus: list[str]) -> list[str]:
    evidence = [title]
    for key in focus:
        if key in metrics:
            evidence.append(f"{key.replace('_', ' ').title()}: {_format_number(metrics[key])}")
    return evidence


def build_actionable_insights(summary: dict[str, Any]) -> list[ActionableInsight]:
    insights: list[ActionableInsight] = []

    attacking = summary.get("attacking", {})
    passing_metrics = attacking.get("metrics", {})
    central_players = attacking.get("central_players", [])
    if central_players:
        headline = f"Build-up flowed through {_join_players(central_players[:3])}."
        recommendation = (
            f"Use {central_players[0]} as the anchor for the attacking narrative and "
            "treat that player as the primary reference point when describing progression."
        )
    else:
        headline = "The passing network does not yet show a clear central hub."
        recommendation = (
            "Describe the structure as distributed until the real adjacency matrix exposes a buildup hub."
        )
    insights.append(
        ActionableInsight(
            section="attacking",
            headline=headline,
            evidence=_as_metric_block(
                "Passing network evidence",
                passing_metrics,
                ["event_count", "node_count", "edge_count"],
            )
            + [f"Central players: {_join_players(central_players[:3])}"],
            implication=(
                "A compact network usually indicates controlled circulation and predictable connections."
                if passing_metrics.get("node_count", 0) and passing_metrics.get("edge_count", 0)
                else "The network remains too thin to infer a stable buildup pattern."
            ),
            recommendation=recommendation,
            confidence="medium" if central_players or passing_metrics.get("event_count") else "low",
        )
    )

    defensive = summary.get("defensive", {})
    defensive_metrics = defensive.get("metrics", {})
    compactness = float(defensive_metrics.get("compactness", 0.0) or 0.0)
    line_stretch = float(defensive_metrics.get("line_stretch", 0.0) or 0.0)
    if compactness >= 0.7:
        headline = "The defensive block stayed compact and difficult to play through."
        recommendation = "Frame the defence as organised and resistant to central penetration."
    elif line_stretch >= 0.5:
        headline = "The defensive line was stretched, exposing gaps between units."
        recommendation = "Call out vulnerability in the space between midfield and defence."
    else:
        headline = "The defensive spacing was inconclusive from the available data."
        recommendation = "Keep the defensive description cautious until spatial data is richer."
    insights.append(
        ActionableInsight(
            section="defensive",
            headline=headline,
            evidence=_as_metric_block(
                "Defensive spacing evidence",
                defensive_metrics,
                ["event_count", "line_stretch", "compactness"],
            ),
            implication=(
                "Compact teams are harder to break through centrally and force opponents wide."
                if compactness >= 0.7
                else "Stretched teams invite combinations between the lines and through-ball opportunities."
            ),
            recommendation=recommendation,
            confidence="medium" if defensive_metrics.get("event_count") else "low",
        )
    )

    player = summary.get("players", {})
    player_metrics = player.get("metrics", {})
    players = player.get("players", [])
    top_player = players[0] if players else {}
    top_player_name = top_player.get("name") if isinstance(top_player, dict) else ""
    headline = (
        f"{top_player_name} drove the attacking output."
        if top_player_name
        else "No player stood out strongly in the current summary."
    )
    recommendation = (
        f"Use {top_player_name} as the lead example for individual impact."
        if top_player_name
        else "Frame the player section around shared responsibility rather than a single star."
    )
    insights.append(
        ActionableInsight(
            section="players",
            headline=headline,
            evidence=_as_metric_block(
                "Player impact evidence",
                player_metrics,
                ["event_count", "xg_contribution", "key_passes", "possession_share"],
            )
            + ([f"Top player: {top_player_name}"] if top_player_name else []),
            implication=(
                "A dominant player usually signals where the attack is being funnelled."
                if top_player_name
                else "The current data is not sufficient to isolate a clear player-led pattern."
            ),
            recommendation=recommendation,
            confidence="medium" if player_metrics.get("event_count") else "low",
        )
    )

    tempo = summary.get("tempo", {})
    tempo_metrics = tempo.get("metrics", {})
    avg_sequence_length = float(tempo_metrics.get("avg_sequence_length", 0.0) or 0.0)
    transition_speed = float(tempo_metrics.get("transition_speed", 0.0) or 0.0)
    if avg_sequence_length >= 6:
        headline = "Possessions were sustained and built through longer sequences."
        recommendation = "Describe the team as patient in buildup and capable of circulating the ball."
    elif transition_speed >= 0.5:
        headline = "The side moved quickly into transition once possession changed."
        recommendation = "Emphasise directness and quick vertical attacks in the report."
    else:
        headline = "The tempo signal is currently too weak to support a strong style claim."
        recommendation = "Keep the tempo paragraph grounded and avoid overclaiming."
    insights.append(
        ActionableInsight(
            section="tempo",
            headline=headline,
            evidence=_as_metric_block(
                "Tempo evidence",
                tempo_metrics,
                ["event_count", "avg_sequence_length", "transition_speed"],
            ),
            implication=(
                "Longer sequences typically indicate control, while shorter ones often signal direct play."
                if avg_sequence_length or transition_speed
                else "There is not yet enough sequencing data to infer tempo reliably."
            ),
            recommendation=recommendation,
            confidence="medium" if tempo_metrics.get("event_count") else "low",
        )
    )

    return insights


def build_llm_insight_payload(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "match_summary": summary,
        "themes": summary.get("themes", []),
        "evidence": summary.get("evidence", []),
    }
