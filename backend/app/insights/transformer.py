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
    best_route = attacking.get("best_route", {}) if isinstance(attacking.get("best_route", {}), dict) else {}
    best_sequence = (
        attacking.get("best_sequence", {}) if isinstance(attacking.get("best_sequence", {}), dict) else {}
    )
    sequence_examples = attacking.get("sequence_examples", []) if isinstance(attacking.get("sequence_examples", []), list) else []

    if best_sequence:
        sequence_label = best_sequence.get("sequence_label", "Sequence")
        sequence_type = best_sequence.get("sequence_type", "")
        supporting_players = []
        if sequence_examples:
            supporting_players = [
                player.get("name", "")
                for player in best_route.get("top_passers", [])[:3]
                if isinstance(player, dict) and player.get("name")
            ]
        if sequence_type == "direct_attack":
            headline = "Direct attacks created the clearest attacking gains."
            recommendation = (
                f"Use quicker forward entries and early vertical passes to trigger direct attacks into { _join_players(supporting_players) if supporting_players else 'the front line' }."
            )
            why_it_helps = (
                "Direct attacks exploit space before the defensive block can recover, especially after regains or short restarts."
            )
            how_to_apply = (
                "Keep one runner high, release the first safe forward pass quickly, and make the wide players attack the second ball."
            )
            expected_result = "This should create earlier box entries and force the opposition line to defend facing its own goal."
        elif sequence_type == "counterattack":
            headline = "Counterattacks were the most efficient sequence type."
            recommendation = (
                "On regain, release the first pass immediately into space and let the wide runners attack beyond the ball."
            )
            why_it_helps = (
                "Counterattacks are most effective when the opposition is still stretched and cannot recover its compact shape."
            )
            how_to_apply = (
                "Do not slow the first transition pass, and support it with one central runner and one far-side runner."
            )
            expected_result = "The team should create more broken-field attacks and higher-value shots in transition."
        elif sequence_type == "switch_play":
            headline = "Switches of play created the strongest attacking outcomes."
            recommendation = (
                "Move the ball side to side more aggressively and isolate the weak-side fullback after the switch."
            )
            why_it_helps = (
                "Switches pull the block across the pitch and open space on the far side before the defence can reset."
            )
            how_to_apply = (
                "Hold the near-side overload long enough to attract pressure, then release the opposite wing into space."
            )
            expected_result = "The team should open more crossing lanes and attack the space behind the far-side winger."
        elif sequence_type == "wide_progression":
            side = "left" if "left" in sequence_label.lower() else "right"
            headline = "Wide progression delivered the most effective entries."
            recommendation = (
                f"Keep building the attack down the {side} side and support the {side} fullback and winger with a late-arriving midfielder."
            )
            why_it_helps = (
                "Repeated wide progression pins the fullback and creates clearer crossing or cut-back opportunities."
            )
            how_to_apply = (
                f"Keep the {side} winger high and wide, let the {side} fullback overlap, and time the near-side midfield run into the box."
            )
            expected_result = "This should lead to more controlled entries, better wide overloads, and more dangerous final actions."
        elif sequence_type == "central_progression":
            headline = "Central progression produced the strongest returns."
            recommendation = (
                "Use central combinations to break the first line and feed the next pass into the half-space or striker."
            )
            why_it_helps = (
                "Central progression is most useful when it moves the opposition midfield and opens the next lane behind it."
            )
            how_to_apply = (
                "Create a double pivot or third-man option in midfield, then punch the next pass into the advanced line."
            )
            expected_result = "The team should progress more cleanly through the middle and create better access into the final third."
        else:
            headline = "Buildup sequences dominated the attacking picture."
            recommendation = (
                "Use patient buildup to move the block first, then release the best attacking route once space opens."
            )
            why_it_helps = (
                "Longer buildup phases create more chances to shift the defence and identify the best attacking lane."
            )
            how_to_apply = (
                "Keep circulation stable in the first two thirds, then accelerate once the opponent steps toward the ball."
            )
            expected_result = "The team should create more repeatable access into the final third and fewer forced attacks."
    elif best_route:
        route_label = best_route.get("label", "Attacking route")
        route_key = best_route.get("key", "")
        top_passers = best_route.get("top_passers", [])
        top_receivers = best_route.get("top_receivers", [])
        route_players = _join_players(
            [player.get("name", "") for player in top_passers[:3] if player.get("name")]
        )
        if route_key == "direct_launch":
            headline = "Direct launches created the clearest attacking gains."
            recommendation = (
                f"Use direct launches into {route_players or 'the front line'} to bypass pressure and attack space early."
            )
            why_it_helps = (
                "Long diagonals and early vertical balls can break the opponent's block before it is fully set."
            )
            how_to_apply = (
                "Keep one forward high, time the near-side winger run, and hit the first safe long ball after a regain."
            )
            expected_result = "The team should get earlier entries into advanced areas and more unsettled defensive lines."
        elif "wing" in route_key:
            side = "left" if route_key.startswith("left") else "right"
            headline = f"{route_label} attacks created the strongest returns."
            recommendation = (
                f"Keep building down the {side} side and ask the {side} fullback and wide attacker to create the main overload."
            )
            why_it_helps = (
                "A repeated wide overload can pin the fullback, open the half-space, and create cleaner access to the box."
            )
            how_to_apply = (
                f"Push the {side} fullback higher, keep the winger wide, and let the near-side midfielder arrive late into the lane."
            )
            expected_result = "That should create more box entries and clearer crossing or cut-back situations."
        else:
            headline = f"{route_label} attacks created the strongest returns."
            recommendation = (
                f"Keep attacking through {route_label.lower()} and build the next phase around the players most often using that lane."
            )
            why_it_helps = (
                "The best route is the one that already finds space consistently, so repeating it improves efficiency."
            )
            how_to_apply = (
                "Use the players who appear most often in the route data to keep the circulation stable and repeatable."
            )
            expected_result = "The team should sustain better progression and create a more repeatable attacking pattern."
    elif central_players:
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
    attacking_evidence = _as_metric_block(
        "Attacking route evidence" if best_route else "Passing network evidence",
        best_route if best_route else passing_metrics,
        ["possessions", "box_entries", "shots", "xg", "xg_per_possession", "event_count", "node_count", "edge_count"],
    )
    if central_players:
        attacking_evidence.append(f"Central players: {_join_players(central_players[:3])}")
    if best_route and top_passers:
        attacking_evidence.append(
            "Top passers: " + ", ".join(player.get("name", "") for player in top_passers[:3] if player.get("name"))
        )
    if best_route and top_receivers:
        attacking_evidence.append(
            "Top receivers: " + ", ".join(player.get("name", "") for player in top_receivers[:3] if player.get("name"))
        )
    insights.append(
        ActionableInsight(
            section="attacking",
            headline=headline,
            evidence=attacking_evidence,
            implication=(
                "A repeatable route with higher box entries and xG should be the main attacking pattern."
                if best_route
                else (
                    "A compact network usually indicates controlled circulation and predictable connections."
                    if passing_metrics.get("node_count", 0) and passing_metrics.get("edge_count", 0)
                    else "The network remains too thin to infer a stable buildup pattern."
                )
            ),
            recommendation=recommendation,
            why_it_helps=why_it_helps,
            how_to_apply=how_to_apply,
            expected_result=expected_result,
            confidence="medium" if (best_route or central_players or passing_metrics.get("event_count")) else "low",
        )
    )

    defensive = summary.get("defensive", {})
    defensive_metrics = defensive.get("metrics", {})
    compactness = float(defensive_metrics.get("compactness", 0.0) or 0.0)
    line_stretch = float(defensive_metrics.get("line_stretch", 0.0) or 0.0)
    flank_breakdown = defensive.get("flank_breakdown", []) if isinstance(defensive.get("flank_breakdown", []), list) else []
    zone_breakdown = defensive.get("zone_breakdown", []) if isinstance(defensive.get("zone_breakdown", []), list) else []
    flank_pressure_gaps = (
        defensive.get("flank_pressure_gaps", []) if isinstance(defensive.get("flank_pressure_gaps", []), list) else []
    )
    top_flank = flank_breakdown[0] if flank_breakdown else {}
    weakest_flank = flank_breakdown[-1] if flank_breakdown else {}
    deepest_zone = zone_breakdown[0] if zone_breakdown else {}
    biggest_gap = {}
    for axis_gap in defensive.get("gaps", []):
        if axis_gap.get("gaps"):
            candidate = axis_gap["gaps"][0]
            if not biggest_gap or candidate.get("gap", 0) > biggest_gap.get("gap", 0):
                biggest_gap = candidate
    if compactness >= 0.7:
        if top_flank and weakest_flank and top_flank.get("flank") != weakest_flank.get("flank"):
            headline = f"The defensive block stayed compact, with pressure strongest on the {top_flank.get('flank')} flank."
            recommendation = (
                f"Keep the block compact, but shift the {weakest_flank.get('flank', 'weak')} flank earlier to avoid a soft side."
            )
        else:
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
        if weakest_flank:
            headline = f"The defensive line was stretched, especially on the {weakest_flank.get('flank')} flank."
            recommendation = (
                f"Shorten the distance between the lines and have the {weakest_flank.get('flank')} side tuck in earlier."
            )
        else:
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
                [
                    "event_count",
                    "line_stretch",
                    "compactness",
                    "left_flank_actions",
                    "center_flank_actions",
                    "right_flank_actions",
                    "defensive_third_actions",
                    "middle_third_actions",
                    "attacking_third_actions",
                ],
            ),
            implication=(
                (
                    f"Compact teams are harder to break through centrally and force opponents wide."
                    if compactness >= 0.7
                    else "Stretched teams invite combinations between the lines and through-ball opportunities."
                )
                + (
                    f" The heaviest pressure was on the {top_flank.get('flank', 'unknown')} flank."
                    if top_flank
                    else ""
                )
                + (
                    f" The weakest flank was {weakest_flank.get('flank', 'unknown')}, which suggests where to close the gap."
                    if weakest_flank
                    else ""
                )
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
