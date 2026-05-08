from __future__ import annotations

import json
from typing import Any

from .qwen import QwenUnavailableError, generate_with_qwen


def build_analyst_prompt(payload: dict[str, Any]) -> str:
    compact_payload = {
        "match_summary": payload.get("match_summary", {}),
        "themes": payload.get("themes", []),
        "evidence": payload.get("evidence", []),
    }
    return (
        "You are a professional football tactical analyst. "
        "Explain the tactical significance of the supplied structured match summary "
        "without inventing data or adding generic commentary.\n"
        "Use only the fields in the payload below.\n\n"
        f"{json.dumps(compact_payload, ensure_ascii=False)}"
    )


def generate_tactical_insight(payload: dict[str, Any]) -> str:
    match_summary = payload.get("match_summary", {})
    themes = payload.get("themes", [])
    evidence = payload.get("evidence", [])
    match = match_summary.get("match", {})
    try:
        return generate_with_qwen(payload)
    except QwenUnavailableError:
        return (
            f"Scaffold insight for {match.get('home_team', 'the home side')} vs "
            f"{match.get('away_team', 'the away side')}: "
            f"the LLM will convert {len(themes)} themes and {len(evidence)} evidence items into analyst-style prose."
        )
    except Exception as exc:
        return (
            f"Qwen generation failed for {match.get('home_team', 'the home side')} vs "
            f"{match.get('away_team', 'the away side')}: {exc}"
        )
