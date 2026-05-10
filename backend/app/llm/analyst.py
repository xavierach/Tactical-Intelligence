from __future__ import annotations

import json
from typing import Any

from .qwen import QwenUnavailableError, generate_with_qwen


def build_analyst_prompt(payload: dict[str, Any]) -> str:
    compact_payload = {
        "match_summary": payload.get("match_summary", {}),
        "themes": payload.get("themes", []),
        "evidence": payload.get("evidence", []),
        "insights": payload.get("insights", []),
    }
    return (
        "You are a professional football tactical analyst. "
        "Turn the supplied structured match summary into actionable coaching insight. "
        "For each key theme, explain what the team should do, why that adjustment matters, "
        "how to apply it in practice, and what improvement it should create. "
        "Avoid generic commentary, and do not invent facts beyond the supplied fields.\n"
        "Use only the fields in the payload below.\n"
        "Write in concise analyst language with concrete football actions.\n\n"
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
            f"the LLM will convert {len(themes)} themes, {len(evidence)} evidence items, "
            f"and the structured coaching briefs into recommendations with reasons, application steps, and expected results."
        )
    except Exception as exc:
        return (
            f"Qwen generation failed for {match.get('home_team', 'the home side')} vs "
            f"{match.get('away_team', 'the away side')}: {exc}"
        )
