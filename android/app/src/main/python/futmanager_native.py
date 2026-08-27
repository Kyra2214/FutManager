"""Chaquopy entry point for the offline FutManager engine."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from engine.manager.career import ManagerService
from engine.world.weekly_cycle import WeeklyWorldCycleService
from career_gateway import play_controlled_match


def _connection(database_path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(str(Path(database_path)))
    connection.row_factory = sqlite3.Row
    return connection


def _table_exists(connection: sqlite3.Connection, table: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1", (table,)
    ).fetchone()
    return row is not None


def _number(value: Any, default: int = 0) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _nullable_number(value: Any) -> int | None:
    return None if value is None else _number(value)


def _text(value: Any, default: str = "") -> str:
    return default if value is None else str(value)


def _controlled_club(connection: sqlite3.Connection) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT career.current_club_id AS club_id, teams.nome AS club_name
        FROM manager_careers career
        LEFT JOIN times teams ON teams.time_id = career.current_club_id
        WHERE career.status='ACTIVE' AND career.current_club_id IS NOT NULL
        ORDER BY career.updated_at DESC, career.career_id DESC
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        return None
    return {"clubId": _number(row["club_id"]), "name": _text(row["club_name"], "Clube controlado")}


def _competition_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    if not _table_exists(connection, "competitions"):
        return []
    entries = "(SELECT COUNT(*) FROM competition_entries entry WHERE entry.competition_id=competition.competition_id)" if _table_exists(connection, "competition_entries") else "0"
    scheduled = "(SELECT COUNT(*) FROM fixtures fixture WHERE fixture.competition_id=competition.competition_id AND fixture.status='SCHEDULED')" if _table_exists(connection, "fixtures") else "0"
    played = "(SELECT COUNT(*) FROM matches game WHERE game.competition_id=competition.competition_id AND game.status='PLAYED')" if _table_exists(connection, "matches") else "0"
    rows = connection.execute(
        f"""
        SELECT competition.competition_id, competition.name, competition.type,
               competition.format, competition.status, competition.season_id,
               season.year AS season_year,
               {entries} AS registered_clubs,
               {scheduled} AS scheduled_fixtures,
               {played} AS played_matches
        FROM competitions competition
        LEFT JOIN seasons season ON season.season_id=competition.season_id
        ORDER BY CASE competition.status WHEN 'ACTIVE' THEN 0 WHEN 'PLANNED' THEN 1 ELSE 2 END,
                 season.year DESC, competition.competition_id DESC
        """
    ).fetchall()
    return [
        {
            "competitionId": _number(row["competition_id"]),
            "name": _text(row["name"], "Competição"),
            "type": _text(row["type"], "NACIONAL"),
            "format": _text(row["format"], "Pontos corridos"),
            "status": _text(row["status"], "ACTIVE"),
            "seasonId": _number(row["season_id"], 0),
            "seasonYear": _nullable_number(row["season_year"]),
            "registeredClubs": _number(row["registered_clubs"]),
            "scheduledFixtures": _number(row["scheduled_fixtures"]),
            "playedMatches": _number(row["played_matches"]),
            "currentPhase": None,
            "tiebreakers": ["points", "wins", "goal_difference", "goals_for"],
        }
        for row in rows
    ]


def _match_card(row: sqlite3.Row) -> dict[str, Any]:
    status = _text(row["status"], "SCHEDULED").upper()
    home_goals = _nullable_number(row["home_goals"])
    away_goals = _nullable_number(row["away_goals"])
    played = status == "PLAYED" and home_goals is not None and away_goals is not None
    fixture_id = _nullable_number(row["fixture_id"])
    match_id = _nullable_number(row["match_id"])
    return {
        "key": f"match-{match_id}" if match_id is not None else f"fixture-{fixture_id}",
        "matchId": match_id,
        "fixtureId": fixture_id,
        "round": _nullable_number(row["round_number"]),
        "scheduledAt": _text(row["scheduled_at"]),
        "status": status,
        "homeClub": {"clubId": _number(row["home_club_id"]), "name": _text(row["home_club_name"], "Clube")},
        "awayClub": {"clubId": _number(row["away_club_id"]), "name": _text(row["away_club_name"], "Clube")},
        "homeGoals": home_goals,
        "awayGoals": away_goals,
        "isPlayed": played,
    }


def _matches(connection: sqlite3.Connection, competition_id: int) -> list[dict[str, Any]]:
    if not _table_exists(connection, "matches"):
        return []
    fixture_select = """
        SELECT fixture.fixture_id, fixture.match_id, fixture.scheduled_at,
               COALESCE(game.status, fixture.status) AS status,
               round.number AS round_number, fixture.home_club_id,
               home.nome AS home_club_name, fixture.away_club_id,
               away.nome AS away_club_name, game.home_goals, game.away_goals
        FROM fixtures fixture
        LEFT JOIN matches game ON game.match_id=fixture.match_id
        LEFT JOIN competition_rounds round ON round.round_id=fixture.round_id
        INNER JOIN times home ON home.time_id=fixture.home_club_id
        INNER JOIN times away ON away.time_id=fixture.away_club_id
        WHERE fixture.competition_id=?
    """ if _table_exists(connection, "fixtures") else ""
    standalone = """
        SELECT NULL AS fixture_id, game.match_id, game.match_date AS scheduled_at,
               game.status, game.round AS round_number, game.home_club_id,
               home.nome AS home_club_name, game.away_club_id,
               away.nome AS away_club_name, game.home_goals, game.away_goals
        FROM matches game
        INNER JOIN times home ON home.time_id=game.home_club_id
        INNER JOIN times away ON away.time_id=game.away_club_id
        WHERE game.competition_id=?
          AND NOT EXISTS (SELECT 1 FROM fixtures fixture WHERE fixture.match_id=game.match_id)
    """
    sql = f"{fixture_select} UNION ALL {standalone} ORDER BY scheduled_at ASC, round_number ASC" if fixture_select else standalone + " ORDER BY scheduled_at ASC, round_number ASC"
    params = (competition_id, competition_id) if fixture_select else (competition_id,)
    return [_match_card(row) for row in connection.execute(sql, params).fetchall()]


def _standings(connection: sqlite3.Connection, competition_id: int, controlled_club_id: int | None) -> list[dict[str, Any]]:
    if not _table_exists(connection, "team_competition_stats"):
        return []
    rows = connection.execute(
        """
        SELECT stats.club_id, teams.nome AS club_name, stats.played, stats.wins,
               stats.draws, stats.losses, stats.goals_for, stats.goals_against,
               stats.points, (stats.goals_for-stats.goals_against) AS goal_difference
        FROM team_competition_stats stats
        INNER JOIN times teams ON teams.time_id=stats.club_id
        WHERE stats.competition_id=?
        ORDER BY stats.points DESC, stats.wins DESC, goal_difference DESC,
                 stats.goals_for DESC, teams.nome ASC
        """,
        (competition_id,),
    ).fetchall()
    result = []
    for position, row in enumerate(rows, start=1):
        club_id = _number(row["club_id"])
        result.append({
            "position": position,
            "clubId": club_id,
            "clubName": _text(row["club_name"], f"Clube #{club_id}"),
            "played": _number(row["played"]),
            "wins": _number(row["wins"]),
            "draws": _number(row["draws"]),
            "losses": _number(row["losses"]),
            "goalsFor": _number(row["goals_for"]),
            "goalsAgainst": _number(row["goals_against"]),
            "goalDifference": _number(row["goal_difference"]),
            "points": _number(row["points"]),
            "isControlledClub": club_id == controlled_club_id,
        })
    return result


def _advance_until_match(connection: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    match_id = _number(payload.get("matchId"))
    if match_id <= 0:
        raise ValueError("MATCH_NOT_FOUND")
    max_weeks = 52
    weeks_advanced = 0
    cycles: list[dict[str, Any]] = []
    base_seed = payload.get("seed")
    for attempt in range(max_weeks + 1):
        dashboard = _dashboard(connection, {})
        fixture = next((item for item in dashboard["upcomingFixtures"] if item["matchId"] == match_id), None)
        if fixture is not None:
            return {
                "status": "READY_FOR_CONTROLLED_MATCH",
                "match_id": match_id,
                "weeks_advanced": weeks_advanced,
                "target_season": dashboard["selectedCompetition"].get("seasonYear") if dashboard["selectedCompetition"] else None,
                "target_round": fixture["round"],
                "cycles": cycles,
                "notice": "Há atividades da carreira que podem permanecer pendentes, mas isso não impede a ida para a partida." if weeks_advanced else None,
            }
        if attempt == max_weeks:
            break
        seed = _number(base_seed) + attempt if base_seed is not None else None
        cycle = WeeklyWorldCycleService(connection).advance_week(seed)
        weeks_advanced += 1
        cycles.append({
            "season": _number(cycle.get("season")),
            "week": _number(cycle.get("week")),
            "matches": _number(cycle.get("matches")),
            "world_events": cycle.get("world_events") or [],
        })
    raise ValueError("MATCH_NOT_FOUND")


def _dashboard(connection: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    competitions = _competition_rows(connection)
    requested_id = _number(payload.get("competitionId"), 0) or None
    selected = next((item for item in competitions if item["competitionId"] == requested_id), None) if requested_id else None
    selected = selected or (competitions[0] if competitions else None)
    controlled = _controlled_club(connection)
    if selected is None:
        return {
            "filters": {"competitionId": requested_id, "season": None, "phaseId": None},
            "source": {"mode": "LOCAL_READ_ONLY_SQLITE", "available": True, "message": "Ainda não há competições persistidas na carreira.", "generatedAt": "offline"},
            "controlledClub": controlled,
            "competitions": [], "selectedCompetitionId": None, "selectedCompetition": None,
            "standings": [], "upcomingFixtures": [], "recentResults": [],
        }
    all_matches = _matches(connection, selected["competitionId"])
    return {
        "filters": {"competitionId": selected["competitionId"], "season": selected["seasonYear"], "phaseId": None},
        "source": {"mode": "LOCAL_READ_ONLY_SQLITE", "available": True, "message": "Consulta direta ao GameState SQLite do dispositivo.", "generatedAt": "offline"},
        "controlledClub": controlled,
        "competitions": competitions,
        "selectedCompetitionId": selected["competitionId"],
        "selectedCompetition": selected,
        "standings": _standings(connection, selected["competitionId"], controlled["clubId"] if controlled else None),
        "upcomingFixtures": [match for match in all_matches if not match["isPlayed"]],
        "recentResults": [match for match in reversed(all_matches) if match["isPlayed"]],
    }


def execute(action: str, payload_json: str, database_path: str) -> str:
    payload: dict[str, Any] = json.loads(payload_json or "{}")
    connection = _connection(database_path)
    try:
        if action == "getDashboard":
            result = _dashboard(connection, payload)
        elif action == "advanceUntilMatch":
            result = _advance_until_match(connection, payload)
        elif action == "playControlledMatch":
            decision = payload.get("decision") if isinstance(payload.get("decision"), dict) else {}
            result = play_controlled_match(connection, {
                "match_id": payload.get("matchId"),
                "seed": payload.get("seed"),
                "decisions": decision,
            })
        elif action == "startCareer":
            result = ManagerService(connection).start_career(
                manager_name=payload.get("managerName"),
                nationality=payload.get("nationality"),
                age=payload.get("age"),
                career_name=payload.get("careerName"),
                target_type=payload.get("targetType", "club"),
                target_id=payload.get("targetId"),
                selected_country_ids=payload.get("selectedCountryIds"),
            )
        elif action == "advanceWeek":
            result = WeeklyWorldCycleService(connection).advance_week(payload.get("seed"))
        else:
            raise ValueError(f"NATIVE_ENGINE_ACTION_UNSUPPORTED:{action}")
        return json.dumps({"ok": True, **result}, ensure_ascii=False)
    except Exception as error:
        connection.rollback()
        return json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False)
    finally:
        connection.close()
