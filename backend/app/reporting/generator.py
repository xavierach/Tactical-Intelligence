from __future__ import annotations

from typing import Any, Iterable

from ..analytics.defensive_spacing import analyze_defensive_spacing
from ..analytics.passing_network import analyze_passing_network
from ..analytics.player_impact import analyze_player_impact
from ..analytics.tempo import analyze_possession_tempo
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

    analytics = {
        "passing_network": analyze_passing_network(event_list),
        "defensive_spacing": analyze_defensive_spacing(event_list),
        "player_impact": analyze_player_impact(event_list),
        "tempo": analyze_possession_tempo(event_list),
    }
    match_summary = build_match_summary(match.to_dict(), analytics)
    summary_dict = match_summary.to_dict()
    insights = build_actionable_insights(summary_dict)
    llm_payload = build_llm_insight_payload(summary_dict)

    sections = [
        ReportSection(
            title="Match Overview",
            summary="High-level context for the fixture and its main tactical shape.",
            bullets=[
                f"Competition: {match.competition}",
                f"Season: {match.season}",
                f"Report focus: {focus_team}",
                "This section will summarize the game state and headline patterns for the selected team.",
            ],
        ),
        ReportSection(
            title="Attacking Analysis",
            summary="How the team progressed the ball and created chances.",
            bullets=[
                f"Summarise buildup structure and overloads for {focus_team}.",
                f"Highlight central playmakers and key passing lanes used by {focus_team}.",
            ],
        ),
        ReportSection(
            title="Defensive Analysis",
            summary="How the team defended space, shape, and transitions.",
            bullets=[
                f"Describe spacing, compactness, and defensive line behaviour for {focus_team}.",
                f"Identify vulnerable zones and repeated exposure patterns around {focus_team}.",
            ],
        ),
        ReportSection(
            title="Key Players",
            summary="The players who most influenced the match story.",
            bullets=[
                f"Rank players by impact, involvement, and tactical importance for {focus_team}.",
                f"Call out the players that shaped possession and pressing phases for {focus_team}.",
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
        "The prompt is reduced to match_summary, themes, and evidence only.",
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
