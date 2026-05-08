from __future__ import annotations

from typing import Any, Iterable

from ..analytics.defensive_spacing import analyze_defensive_spacing
from ..analytics.passing_network import analyze_passing_network
from ..analytics.player_impact import analyze_player_impact
from ..analytics.tempo import analyze_possession_tempo
from ..data.statsbomb_loader import load_match_lineups
from ..domain import MatchContext, ReportSection, TacticalReport
from ..insights.transformer import build_actionable_insights, build_llm_insight_payload
from ..summary.matcher import build_match_summary
from ..llm.analyst import generate_tactical_insight


def generate_tactical_report(
    match: MatchContext,
    events: Iterable[dict[str, Any]] | None = None,
) -> TacticalReport:
    event_list = list(events or [])
    focus_team = match.focus_team or match.home_team
    lineups = load_match_lineups(match.match_id)

    analytics = {
        "passing_network": analyze_passing_network(
            event_list,
            focus_team=focus_team,
            lineups=lineups,
        ),
        "defensive_spacing": analyze_defensive_spacing(event_list, focus_team=focus_team),
        "player_impact": analyze_player_impact(event_list, focus_team=focus_team),
        "tempo": analyze_possession_tempo(event_list, focus_team=focus_team),
    }
    match_summary = build_match_summary(match.to_dict(), analytics)
    summary_dict = match_summary.to_dict()
    insights = build_actionable_insights(summary_dict)
    llm_payload = build_llm_insight_payload(summary_dict)

    match_block = summary_dict.get("match", {})
    attacking_summary = summary_dict.get("attacking", {})
    defensive_summary = summary_dict.get("defensive", {})
    players_summary = summary_dict.get("players", {})
    tempo_summary = summary_dict.get("tempo", {})
    themes = summary_dict.get("themes", [])
    evidence = summary_dict.get("evidence", [])

    sections = [
        ReportSection(
            title="Match Overview",
            summary=(
                f"Selected team: {focus_team}. "
                f"{themes[0] if themes else 'High-level fixture context.'}"
            ),
            bullets=[
                f"Competition: {match_block.get('competition', match.competition)}",
                f"Season: {match_block.get('season', match.season)}",
                f"Report focus: {match_block.get('focus_team', focus_team)}",
                f"Confidence: {summary_dict.get('confidence', 'medium')}",
            ],
        ),
        ReportSection(
            title="Attacking Analysis",
            summary=attacking_summary.get("summary", "How the team progressed the ball and created chances."),
            bullets=[
                attacking_summary.get("headline", f"{focus_team} built through central combinations."),
                f"Central players: {', '.join(attacking_summary.get('central_players', [])[:3]) or 'None identified'}",
                f"Top connection count: {len(attacking_summary.get('top_connections', []))}",
            ],
        ),
        ReportSection(
            title="Defensive Analysis",
            summary=defensive_summary.get("summary", "How the team defended space, shape, and transitions."),
            bullets=[
                defensive_summary.get("headline", f"{focus_team} showed a defensive spacing pattern."),
                f"Compactness: {defensive_summary.get('metrics', {}).get('compactness', 0):.2f}",
                f"Line stretch: {defensive_summary.get('metrics', {}).get('line_stretch', 0):.2f}",
                f"Spacing gaps analysed: {len(defensive_summary.get('gaps', []))}",
            ],
        ),
        ReportSection(
            title="Key Players",
            summary=players_summary.get("summary", "The players who most influenced the match story."),
            bullets=[
                players_summary.get("headline", "No single player clearly dominated."),
                f"Top player: {(players_summary.get('top_player', {}) or {}).get('name', 'None identified')}",
                f"xG contribution: {players_summary.get('metrics', {}).get('xg_contribution', 0):.2f}",
            ],
        ),
        ReportSection(
            title="Tempo and Transitions",
            summary=tempo_summary.get("summary", "How the team controlled or accelerated possession."),
            bullets=[
                tempo_summary.get("headline", f"{focus_team} showed a mixed tempo profile."),
                f"Possessions: {tempo_summary.get('metrics', {}).get('possession_count', 0)}",
                f"Average sequence length: {tempo_summary.get('metrics', {}).get('avg_sequence_length', 0):.2f}",
                f"Transition speed: {tempo_summary.get('metrics', {}).get('transition_speed', 0):.2f}",
            ],
        ),
    ]

    visualisations = [
        {
            "id": "passing-network",
            "title": "Passing Network",
            "description": "Player connectivity and buildup structure.",
        },
        {
            "id": "defensive-spacing",
            "title": "Defensive Spacing",
            "description": "Spatial gaps and line stretch analysis.",
        },
    ]

    notes = [
        generate_tactical_insight(llm_payload),
        f"Prepared {len(insights)} structured insights from {len(summary_dict.get('themes', []))} themes.",
        f"Evidence count available to the backend summary: {len(evidence)}.",
        f"Report focus team: {focus_team}.",
    ]

    return TacticalReport(
        match=match,
        sections=sections,
        analytics=analytics,
        summary=summary_dict,
        insights=[insight.to_dict() for insight in insights],
        visualisations=visualisations,
        notes=notes,
    )
