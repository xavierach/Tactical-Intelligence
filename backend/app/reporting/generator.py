from __future__ import annotations

from typing import Any, Iterable

from ..analytics.defensive_spacing import analyze_defensive_spacing
from ..analytics.passing_network import analyze_passing_network
from ..analytics.player_impact import analyze_player_impact
from ..analytics.tempo import analyze_possession_tempo
from ..domain import MatchContext, ReportSection, TacticalReport
from ..llm.analyst import generate_tactical_insight


def generate_tactical_report(
    match: MatchContext,
    events: Iterable[dict[str, Any]] | None = None,
) -> TacticalReport:
    event_list = list(events or [])

    analytics = {
        "passing_network": analyze_passing_network(event_list),
        "defensive_spacing": analyze_defensive_spacing(event_list),
        "player_impact": analyze_player_impact(event_list),
        "tempo": analyze_possession_tempo(event_list),
    }

    sections = [
        ReportSection(
            title="Match Overview",
            summary="High-level context for the fixture and its main tactical shape.",
            bullets=[
                f"Competition: {match.competition}",
                f"Season: {match.season}",
                "This section will summarize the game state and headline patterns.",
            ],
        ),
        ReportSection(
            title="Attacking Analysis",
            summary="How the team progressed the ball and created chances.",
            bullets=[
                "Summarise buildup structure and overloads.",
                "Highlight central playmakers and key passing lanes.",
            ],
        ),
        ReportSection(
            title="Defensive Analysis",
            summary="How the team defended space, shape, and transitions.",
            bullets=[
                "Describe spacing, compactness, and defensive line behaviour.",
                "Identify vulnerable zones and repeated exposure patterns.",
            ],
        ),
        ReportSection(
            title="Key Players",
            summary="The players who most influenced the match story.",
            bullets=[
                "Rank players by impact, involvement, and tactical importance.",
                "Call out the players that shaped possession and pressing phases.",
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
        generate_tactical_insight(match.to_dict(), analytics),
        "This report is scaffolded for now and will become fully data-driven as analytics are wired in.",
    ]

    return TacticalReport(
        match=match,
        sections=sections,
        analytics=analytics,
        visualisations=visualisations,
        notes=notes,
    )
