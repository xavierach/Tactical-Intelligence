from __future__ import annotations

from typing import Any, List

from .matcher import MatchSummary, build_match_summary


def build_match_summary_payload(match: dict[str, Any], analytics: dict[str, Any]) -> dict[str, Any]:
    return build_match_summary(match, analytics).to_dict()
