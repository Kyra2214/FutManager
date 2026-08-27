from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass
from typing import Any

from engine.world.time_and_finance import FinanceLedger, WorldTickContext


TRAVEL_SCHEMA = """
CREATE TABLE IF NOT EXISTS travel_cost_configs(
    config_id INTEGER PRIMARY KEY CHECK(config_id=1),
    domestic_cost INTEGER NOT NULL DEFAULT 25000 CHECK(domestic_cost >= 0),
    international_cost INTEGER NOT NULL DEFAULT 100000 CHECK(international_cost >= 0),
    updated_at TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class TravelEstimate:
    match_id: int
    club_id: int
    opponent_id: int
    route_type: str
    cost: int
    currency: str
    available: bool
    reason: str | None = None


class TravelCostService:
    """Custos de deslocamento derivados de clubes/países persistidos e do ledger."""

    def __init__(self, connection: Any):
        self.connection = connection
        self.ledger = FinanceLedger(connection)
        self.connection.executescript(TRAVEL_SCHEMA)
        self.connection.execute(
            "INSERT OR IGNORE INTO travel_cost_configs(config_id,domestic_cost,international_cost,updated_at) VALUES(1,25000,100000,date('now'))"
        )
        self.connection.commit()

    def _config(self) -> Any:
        return self.connection.execute("SELECT * FROM travel_cost_configs WHERE config_id=1").fetchone()

    def _club_country(self, club_id: int) -> int | None:
        row = self.connection.execute("SELECT pais_id FROM times WHERE time_id=?", (club_id,)).fetchone()
        if not row or row[0] is None:
            return None
        return int(row[0])

    def estimate(self, match_id: int, club_id: int | None = None) -> TravelEstimate:
        match = self.connection.execute("SELECT match_id,home_club_id,away_club_id FROM matches WHERE match_id=?", (match_id,)).fetchone()
        if not match:
            return TravelEstimate(match_id, int(club_id or 0), 0, "UNAVAILABLE", 0, FinanceLedger.CURRENCY, False, "MATCH_NOT_FOUND")
        home_id, away_id = int(match[1]), int(match[2])
        selected = int(club_id) if club_id is not None else away_id
        if selected not in (home_id, away_id):
            return TravelEstimate(match_id, selected, 0, "UNAVAILABLE", 0, FinanceLedger.CURRENCY, False, "CLUB_NOT_IN_MATCH")
        opponent = home_id if selected == away_id else away_id
        if selected == home_id:
            return TravelEstimate(match_id, selected, opponent, "HOME_NO_TRAVEL", 0, FinanceLedger.CURRENCY, True)
        selected_country = self._club_country(selected)
        opponent_country = self._club_country(opponent)
        if selected_country is None or opponent_country is None:
            return TravelEstimate(match_id, selected, opponent, "UNAVAILABLE", 0, FinanceLedger.CURRENCY, False, "CLUB_COUNTRY_UNAVAILABLE")
        config = self._config()
        route_type = "DOMESTIC" if selected_country == opponent_country else "INTERNATIONAL"
        cost = int(config[1] if route_type == "DOMESTIC" else config[2])
        return TravelEstimate(match_id, selected, opponent, route_type, cost, FinanceLedger.CURRENCY, True)

    def preview(self, match_id: int, club_id: int | None = None) -> dict[str, Any]:
        estimate = self.estimate(match_id, club_id)
        return {
            "status": "AVAILABLE" if estimate.available else "UNAVAILABLE",
            "match_id": estimate.match_id,
            "club_id": estimate.club_id,
            "opponent_id": estimate.opponent_id,
            "route_type": estimate.route_type,
            "cost": estimate.cost,
            "currency": estimate.currency,
            "reason": estimate.reason,
            "persisted": False,
        }

    def post_for_match(self, match_id: int, context: WorldTickContext, managed_transaction: bool = True) -> dict[str, Any]:
        estimate = self.estimate(match_id)
        if not estimate.available or estimate.cost <= 0 or estimate.route_type == "HOME_NO_TRAVEL":
            return {**self.preview(match_id), "status": "SKIPPED", "persisted": False}
        with (self.connection if managed_transaction else nullcontext()):
            posted = self.ledger.post(
                context,
                estimate.club_id,
                "EXPENSE",
                "TRAVEL",
                -estimate.cost,
                "travel",
                str(match_id),
                f"Deslocamento {estimate.route_type.lower()} para partida {match_id}",
            )
            if not posted:
                return {**self.preview(match_id), "status": "ALREADY_PROCESSED", "persisted": True}
            state = self.connection.execute("SELECT 1 FROM club_economic_state WHERE club_id=?", (estimate.club_id,)).fetchone()
            if state:
                self.connection.execute(
                    "UPDATE club_economic_state SET cash=cash-?,updated_at=? WHERE club_id=?",
                    (estimate.cost, context.current_date.isoformat(), estimate.club_id),
                )
        return {**self.preview(match_id), "status": "PROCESSED", "persisted": True}

    def club_summary(self, club_id: int, season: int | None = None) -> dict[str, Any]:
        where = "club_id=? AND category='TRAVEL'"
        args: list[Any] = [club_id]
        if season is not None:
            where += " AND season=?"
            args.append(season)
        row = self.connection.execute(
            f"SELECT COUNT(*) AS trips, COALESCE(SUM(-amount),0) AS total_cost FROM financial_ledger WHERE {where}",
            tuple(args),
        ).fetchone()
        return {
            "club_id": club_id,
            "season": season,
            "trips": int(row[0]),
            "total_cost": int(row[1]),
            "currency": FinanceLedger.CURRENCY,
            "source": "financial_ledger",
        }
