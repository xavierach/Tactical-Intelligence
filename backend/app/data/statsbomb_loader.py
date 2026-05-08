from __future__ import annotations

from functools import lru_cache
from typing import Any

import pandas as pd
from statsbombpy import sb

FALLBACK_COMPETITIONS: list[dict[str, Any]] = [
    {
        "competition_id": 1,
        "season_id": 1,
        "competition_name": "Demo League",
        "season_name": "2024/25",
        "country_name": "Demo",
        "match_updated": "",
        "match_available": "",
    }
]

FALLBACK_MATCHES: dict[tuple[int, int], list[dict[str, Any]]] = {
    (1, 1): [
        {
            "match_id": 1000001,
            "competition_id": 1,
            "season_id": 1,
            "competition_name": "Demo League",
            "season_name": "2024/25",
            "home_team": "Barcelona",
            "away_team": "Real Madrid",
            "match_date": "2024-03-02",
            "kick_off": "20:00:00.000",
        },
        {
            "match_id": 1000002,
            "competition_id": 1,
            "season_id": 1,
            "competition_name": "Demo League",
            "season_name": "2024/25",
            "home_team": "Liverpool",
            "away_team": "Manchester City",
            "match_date": "2024-03-09",
            "kick_off": "18:30:00.000",
        },
    ]
}


@lru_cache(maxsize=1)
def list_competitions() -> list[dict[str, Any]]:
    try:
        competitions = sb.competitions()
    except Exception:
        return FALLBACK_COMPETITIONS

    if competitions.empty:
        return FALLBACK_COMPETITIONS

    columns = [
        "competition_id",
        "season_id",
        "competition_name",
        "season_name",
        "country_name",
        "match_updated",
        "match_available",
    ]
    available = [column for column in columns if column in competitions.columns]
    return competitions.loc[:, available].fillna("").to_dict(orient="records")


@lru_cache(maxsize=64)
def list_matches(competition_id: int, season_id: int) -> list[dict[str, Any]]:
    try:
        matches = sb.matches(competition_id=competition_id, season_id=season_id)
    except Exception:
        return FALLBACK_MATCHES.get((competition_id, season_id), [])

    if matches.empty:
        return FALLBACK_MATCHES.get((competition_id, season_id), [])

    columns = [
        "match_id",
        "match_date",
        "kick_off",
        "home_team",
        "away_team",
        "competition",
        "season",
        "competition_stage",
    ]
    available = [column for column in columns if column in matches.columns]
    match_frame = matches.loc[:, available].copy()
    if "competition" in match_frame.columns:
        match_frame["competition_name"] = match_frame["competition"].apply(
            lambda value: value.get("competition_name") if isinstance(value, dict) else value
        )
        match_frame["competition_id"] = match_frame["competition"].apply(
            lambda value: value.get("competition_id") if isinstance(value, dict) else competition_id
        )
        match_frame = match_frame.drop(columns=["competition"])
    else:
        match_frame["competition_name"] = ""
        match_frame["competition_id"] = competition_id

    if "season" in match_frame.columns:
        match_frame["season_name"] = match_frame["season"].apply(
            lambda value: value.get("season_name") if isinstance(value, dict) else value
        )
        match_frame["season_id"] = match_frame["season"].apply(
            lambda value: value.get("season_id") if isinstance(value, dict) else season_id
        )
        match_frame = match_frame.drop(columns=["season"])
    else:
        match_frame["season_name"] = ""
        match_frame["season_id"] = season_id

    if "home_team" in match_frame.columns:
        match_frame["home_team"] = match_frame["home_team"].apply(
            lambda value: value.get("home_team_name") if isinstance(value, dict) else value
        )
    if "away_team" in match_frame.columns:
        match_frame["away_team"] = match_frame["away_team"].apply(
            lambda value: value.get("away_team_name") if isinstance(value, dict) else value
        )

    return match_frame.fillna("").to_dict(orient="records")


@lru_cache(maxsize=256)
def load_match_events(match_id: str) -> list[dict[str, Any]]:
    try:
        events = sb.events(match_id=match_id)
    except Exception:
        return []

    if isinstance(events, pd.DataFrame):
        return events.fillna("").to_dict(orient="records")
    return list(events)


@lru_cache(maxsize=64)
def load_match_lineups(match_id: str) -> list[dict[str, Any]]:
    try:
        lineups = sb.lineups(match_id=match_id)
    except Exception:
        return []

    if isinstance(lineups, pd.DataFrame):
        return lineups.fillna("").to_dict(orient="records")

    if isinstance(lineups, dict):
        records: list[dict[str, Any]] = []
        for team_name, team_value in lineups.items():
            if isinstance(team_value, pd.DataFrame):
                team_records = team_value.fillna("").to_dict(orient="records")
                for record in team_records:
                    record.setdefault("team_name", team_name)
                records.extend(team_records)
            elif isinstance(team_value, list):
                for record in team_value:
                    if isinstance(record, dict):
                        record = dict(record)
                        record.setdefault("team_name", team_name)
                        records.append(record)
        return records

    return list(lineups)
