from __future__ import annotations

from typing import Any


def build_analyst_prompt(match: dict[str, Any], analytics: dict[str, Any]) -> str:
    return (
        "You are a professional football tactical analyst. "
        "Explain the tactical significance of the supplied structured analytics "
        "without inventing data or adding generic commentary.\n\n"
        f"Match context: {match}\n"
        f"Analytics payload: {analytics}"
    )


def generate_tactical_insight(match: dict[str, Any], analytics: dict[str, Any]) -> str:
    return (
        f"Scaffold insight for {match.get('home_team', 'the home side')} vs "
        f"{match.get('away_team', 'the away side')}: "
        "the LLM integration will convert structured metrics into analyst-style prose."
    )
