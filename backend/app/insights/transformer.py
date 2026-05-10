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
    why_it_helps: str = ""
    how_to_apply: str = ""
    expected_result: str = ""
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
            f"Use {central_players[0]} as the anchor for progression and create overloads around that player."
        )
        why_it_helps = (
            "Anchoring the attack around the most connected player gives the team a clearer passing reference "
            "and makes it harder for the opponent to predict where the next action starts."
        )
        how_to_apply = (
            "Build the first and second phase of possession through that hub, then rotate a nearby midfielder or "
            "fullback into the next lane to create a third-man option."
        )
        expected_result = "This should improve ball retention in buildup and create cleaner access into the final third."
    else:
        headline = "The passing network does not yet show a clear central hub."
        recommendation = (
            "Describe the structure as distributed until the real adjacency matrix exposes a buildup hub."
        )
        why_it_helps = (
            "A distributed structure prevents the report from overclaiming when the network is too sparse to "
            "identify a clear creator."
        )
        how_to_apply = (
            "Look for the player or side that repeatedly receives the second pass after regain, then use that as "
            "the reference point in future reports."
        )
        expected_result = "The report will become more precise once a stable buildup hub is visible."
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
            why_it_helps=why_it_helps,
            how_to_apply=how_to_apply,
            expected_result=expected_result,
            confidence="medium" if central_players or passing_metrics.get("event_count") else "low",
        )
    )

    defensive = summary.get("defensive", {})
    defensive_metrics = defensive.get("metrics", {})
    compactness = float(defensive_metrics.get("compactness", 0.0) or 0.0)
    line_stretch = float(defensive_metrics.get("line_stretch", 0.0) or 0.0)
    if compactness >= 0.7:
        headline = "The defensive block stayed compact and difficult to play through."
        recommendation = "Keep the block compact and shift as a unit when possession is lost."
        why_it_helps = (
            "Compact spacing closes the channels between midfield and defence, which reduces the opponent's "
            "ability to play through the middle."
        )
        how_to_apply = (
            "Push the back line up together, keep the midfield line narrow, and trigger pressure on backwards or "
            "square passes."
        )
        expected_result = "This should reduce gaps between lines and force attacks into lower-value wide areas."
    elif line_stretch >= 0.5:
        headline = "The defensive line was stretched, exposing gaps between units."
        recommendation = "Shorten the distance between the lines and protect the central corridor more aggressively."
        why_it_helps = (
            "A shorter block makes it harder for the opponent to isolate defenders with vertical passes or to "
            "attack the space behind midfield."
        )
        how_to_apply = (
            "Drop the nearest midfielder into the line when the ball is central, and recover the far-side winger "
            "earlier to keep the block connected."
        )
        expected_result = "The team should concede fewer clean entries between the lines and be harder to play through."
    else:
        headline = "The defensive spacing was inconclusive from the available data."
        recommendation = "Keep the defensive description cautious until the team-specific spatial pattern is clearer."
        why_it_helps = (
            "When the data is mixed, cautious language avoids overpromising a tactical adjustment that the match "
            "does not support."
        )
        how_to_apply = (
            "Use the report to track whether the next match produces clearer compactness or stretching signals."
        )
        expected_result = "This keeps the report credible until stronger defensive patterns emerge."
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
            why_it_helps=why_it_helps,
            how_to_apply=how_to_apply,
            expected_result=expected_result,
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
        f"Use {top_player_name} as the lead example for individual impact and attacking responsibility."
        if top_player_name
        else "Frame the player section around shared responsibility rather than a single star."
    )
    why_it_helps = (
        "Building the report around the most influential player makes the tactical story easier to understand and "
        "highlights where the team naturally funnels possession."
        if top_player_name
        else "When no single player dominates, a shared-responsibility description is more accurate."
    )
    how_to_apply = (
        f"Show where {top_player_name} receives the ball, how often they trigger the next action, and which "
        "teammates support them in the next pass."
        if top_player_name
        else "Group the key players by role and explain how the attack is distributed across them."
    )
    expected_result = (
        "This will help identify the main attacking outlet and whether the team is over-reliant on one player."
        if top_player_name
        else "The report will better reflect a balanced attack if responsibility is shared."
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
            why_it_helps=why_it_helps,
            how_to_apply=how_to_apply,
            expected_result=expected_result,
            confidence="medium" if player_metrics.get("event_count") else "low",
        )
    )

    tempo = summary.get("tempo", {})
    tempo_metrics = tempo.get("metrics", {})
    avg_sequence_length = float(tempo_metrics.get("avg_sequence_length", 0.0) or 0.0)
    transition_speed = float(tempo_metrics.get("transition_speed", 0.0) or 0.0)
    if avg_sequence_length >= 6:
        headline = "Possessions were sustained and built through longer sequences."
        recommendation = "Use patient circulation before accelerating into the final third."
        why_it_helps = (
            "Longer sequences can move the opposition block side to side and create a better moment to attack the "
            "space that opens after the shift."
        )
        how_to_apply = (
            "Keep the ball long enough to move the defensive block, then release the next forward pass once a lane "
            "opens."
        )
        expected_result = "This should create more controlled entries and better quality chances."
    elif transition_speed >= 0.5:
        headline = "The side moved quickly into transition once possession changed."
        recommendation = "Trigger immediate vertical runs after regains."
        why_it_helps = (
            "Quick transitions exploit the opponent before they can reset their shape and protect space behind the "
            "ball."
        )
        how_to_apply = (
            "Look for the first forward pass into space or the striker's feet, then support the run with wide "
            "runners."
        )
        expected_result = "The team should create more dangerous attacks while the defence is still disorganised."
    else:
        headline = "The tempo signal is currently too weak to support a strong style claim."
        recommendation = "Keep the tempo paragraph grounded and avoid overclaiming."
        why_it_helps = (
            "A cautious interpretation prevents the report from forcing a tempo identity that the possession data "
            "does not yet support."
        )
        how_to_apply = "Use additional matches to determine whether the team is more patient or more direct."
        expected_result = "The report will become more reliable once a stronger tempo pattern is visible."
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
            why_it_helps=why_it_helps,
            how_to_apply=how_to_apply,
            expected_result=expected_result,
            confidence="medium" if tempo_metrics.get("event_count") else "low",
        )
    )

    return insights


def build_llm_insight_payload(
    summary: dict[str, Any],
    insights: list[ActionableInsight] | None = None,
) -> dict[str, Any]:
    return {
        "match_summary": summary,
        "themes": summary.get("themes", []),
        "evidence": summary.get("evidence", []),
        "insights": [insight.to_dict() for insight in insights or []],
    }
