from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable


PASS_ASSIST_FIELDS = {"pass_shot_assist", "pass_goal_assist"}
SHOT_XG_FIELDS = ("shot_statsbomb_xg", "statsbomb_xg", "shot_xg")
SHOT_KEY_PASS_FIELDS = {"shot_key_pass_id"}


def _string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        for candidate in ("name", "value", "player_name", "team_name"):
            nested = value.get(candidate)
            if nested:
                return str(nested)
        return ""
    return str(value)


def _number(value: Any) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return 0.0
    return 0.0


def _event_type(event: dict[str, Any]) -> str:
    return _string(
        event.get("type")
        or event.get("event_type")
        or event.get("type_name")
        or event.get("sub_type")
    ).lower()


def _player_name(event: dict[str, Any]) -> str:
    return _string(event.get("player") or event.get("player_name"))


def _team_name(event: dict[str, Any]) -> str:
    return _string(event.get("team") or event.get("team_name"))


def _event_possession(event: dict[str, Any]) -> Any:
    return event.get("possession") or event.get("possession_id")


def _pass_payload(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("pass")
    return payload if isinstance(payload, dict) else {}


def _shot_payload(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("shot")
    return payload if isinstance(payload, dict) else {}


def _is_pass(event: dict[str, Any]) -> bool:
    event_type = _event_type(event)
    return "pass" in event_type


def _is_shot(event: dict[str, Any]) -> bool:
    return "shot" in _event_type(event)


def _is_key_pass(event: dict[str, Any]) -> bool:
    if not _is_pass(event):
        return False
    if any(bool(event.get(field)) for field in PASS_ASSIST_FIELDS):
        return True
    payload = _pass_payload(event)
    return bool(payload.get("shot_assist") or payload.get("goal_assist"))


def _shot_xg(event: dict[str, Any]) -> float:
    for field in SHOT_XG_FIELDS:
        if field in event:
            value = _number(event.get(field))
            if value:
                return value
    payload = _shot_payload(event)
    if payload:
        for field in ("statsbomb_xg", "xg", "shot_statsbomb_xg"):
            if field in payload:
                value = _number(payload.get(field))
                if value:
                    return value
    return 0.0


def analyze_player_impact(events: Iterable[dict[str, Any]] | None = None) -> dict[str, Any]:
    event_list = list(events or [])

    player_stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "name": "",
            "team": "",
            "actions": 0,
            "passes": 0,
            "shots": 0,
            "key_passes": 0,
            "assists": 0,
            "xg": 0.0,
            "possession_ids": set(),
        }
    )
    team_action_counts: dict[str, int] = defaultdict(int)
    team_players: dict[str, set[str]] = defaultdict(set)
    total_xg = 0.0
    total_key_passes = 0
    total_shots = 0
    total_actions = 0

    for event in event_list:
        player = _player_name(event)
        team = _team_name(event)
        if not player or not team:
            continue

        stats = player_stats[player]
        stats["name"] = player
        stats["team"] = team
        stats["actions"] += 1
        stats["possession_ids"].add(_event_possession(event))
        team_action_counts[team] += 1
        team_players[team].add(player)
        total_actions += 1

        if _is_pass(event):
            stats["passes"] += 1
            if _is_key_pass(event):
                stats["key_passes"] += 1
                total_key_passes += 1

            pass_payload = _pass_payload(event)
            if bool(pass_payload.get("goal_assist") or event.get("pass_goal_assist")):
                stats["assists"] += 1

        if _is_shot(event):
            stats["shots"] += 1
            total_shots += 1
            shot_xg = _shot_xg(event)
            stats["xg"] += shot_xg
            total_xg += shot_xg

    if not player_stats:
        return {
            "summary": "No player actions with usable names were available.",
            "metrics": {
                "event_count": len(event_list),
                "xg_contribution": 0.0,
                "key_passes": 0,
                "possession_share": 0.0,
                "shot_count": 0,
                "assist_count": 0,
            },
            "players": [],
            "team_breakdown": [],
            "notes": [
                "Player impact needs named players in the event stream.",
                "Once StatsBomb events are loaded, this layer can rank players by action volume, chance creation, and xG.",
            ],
        }

    team_breakdown = []
    for team, count in sorted(team_action_counts.items(), key=lambda item: item[1], reverse=True):
        unique_players = len(team_players[team]) or 1
        team_breakdown.append(
            {
                "team": team,
                "actions": count,
                "players": unique_players,
                "share": round(count / max(total_actions, 1), 3),
            }
        )

    players: list[dict[str, Any]] = []
    for player, stats in player_stats.items():
        possession_share = stats["actions"] / max(total_actions, 1)
        players.append(
            {
                "name": stats["name"],
                "team": stats["team"],
                "actions": stats["actions"],
                "passes": stats["passes"],
                "shots": stats["shots"],
                "key_passes": stats["key_passes"],
                "assists": stats["assists"],
                "xg": round(stats["xg"], 3),
                "possession_share": round(possession_share, 3),
                "impact_score": round(
                    (stats["xg"] * 4.0)
                    + (stats["key_passes"] * 1.5)
                    + (stats["assists"] * 3.0)
                    + (stats["shots"] * 0.75)
                    + (stats["passes"] * 0.05),
                    3,
                ),
                "team_action_share": round(stats["actions"] / max(team_action_counts[stats["team"]], 1), 3),
            }
        )

    players.sort(key=lambda item: (item["impact_score"], item["xg"], item["actions"]), reverse=True)

    top_player = players[0]
    top_team = top_player["team"]
    team_xg = defaultdict(float)
    for player in players:
        team_xg[player["team"]] += player["xg"]

    summary = (
        f"{top_player['name']} led the player-impact view for {top_team}, contributing "
        f"{top_player['xg']:.2f} xG with {top_player['key_passes']} key passes and "
        f"{top_player['shots']} shots."
    )

    return {
        "summary": summary,
        "metrics": {
            "event_count": len(event_list),
            "xg_contribution": round(total_xg, 3),
            "key_passes": total_key_passes,
            "possession_share": round(top_player["possession_share"], 3),
            "shot_count": total_shots,
            "assist_count": sum(player["assists"] for player in players),
            "player_count": len(players),
        },
        "players": players[:10],
        "team_breakdown": team_breakdown,
        "notes": [
            "Player impact is ranked by a blended impact score: xG, key passes, assists, shots, and pass volume.",
            "Possession share is the share of named on-ball actions by each player in the event stream.",
            "Use the top-ranked player and the team breakdown to write the player section of the report.",
        ],
    }
