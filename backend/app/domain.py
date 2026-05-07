from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class MatchContext:
    match_id: str
    competition: str = "StatsBomb Open Data"
    season: str = "Open Data"
    home_team: str = "Home Team"
    away_team: str = "Away Team"
    kickoff: str | None = None
    venue: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ReportSection:
    title: str
    summary: str
    bullets: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TacticalReport:
    match: MatchContext
    sections: list[ReportSection]
    analytics: dict[str, Any]
    visualisations: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "match": self.match.to_dict(),
            "sections": [section.to_dict() for section in self.sections],
            "analytics": self.analytics,
            "visualisations": self.visualisations,
            "notes": self.notes,
        }
