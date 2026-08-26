from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from random import Random
import sqlite3
from contextlib import nullcontext

from engine.economy.institutional_power import InstitutionalPowerService
from engine.economy.staff_market import StaffMarketService
from engine.events.service import ClubEventService
from engine.world.time_and_finance import FinanceLedger, LogicalClock, WorldTickContext


from engine.core.state_store import assert_mutable_state_path
from engine.core.domain_errors import DomainError, DomainErrorCode
FORMULA_VERSION = "sponsorship-f1-inspired-v1"
OFFER_WINDOW_WEEKS = 3
CONTRACT_WEEKS = 6
OFFERS_PER_WINDOW = 3

# Valores de gameplay, ajustados à folha semanal do motor. Não representam
# contratos ou marcas do mundo real.
STAR_RULES = {
    1: {"minimum_overall": 0.0, "upfront": 75_000, "weekly": 15_000, "mission": 50_000},
    2: {"minimum_overall": 16.0, "upfront": 150_000, "weekly": 35_000, "mission": 125_000},
    3: {"minimum_overall": 36.0, "upfront": 320_000, "weekly": 80_000, "mission": 275_000},
    4: {"minimum_overall": 56.0, "upfront": 650_000, "weekly": 160_000, "mission": 600_000},
    5: {"minimum_overall": 72.0, "upfront": 1_200_000, "weekly": 300_000, "mission": 1_100_000},
}

SPONSOR_TEMPLATES = (
    ("lumen", "Lumen", "energia", 1),
    ("ponte", "Ponte", "mobilidade", 1),
    ("nexo", "Nexo", "tecnologia", 2),
    ("safira", "Safira", "varejo", 2),
    ("orbita", "Órbita", "telecom", 3),
    ("verve", "Verve", "bebidas", 3),
    ("alvorada", "Alvorada", "serviços", 4),
    ("cobalto", "Cobalto", "indústria", 4),
    ("aurora", "Aurora", "mobilidade", 5),
    ("vertice", "Vértice", "tecnologia", 5),
)

MISSION_TYPES = ("institutional_overall", "ct_quality", "squad_quality", "match_wins", "goals_scored", "match_attendance")

SCHEMA = """
CREATE TABLE IF NOT EXISTS sponsor_templates(
  sponsor_id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  industry TEXT NOT NULL,
  base_stars INTEGER NOT NULL CHECK(base_stars BETWEEN 1 AND 5),
  generation_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sponsor_offer_sets(
  offer_set_id INTEGER PRIMARY KEY AUTOINCREMENT,
  club_id INTEGER NOT NULL,
  generation INTEGER NOT NULL,
  source_overall REAL NOT NULL,
  source_stars INTEGER NOT NULL,
  created_season INTEGER NOT NULL,
  created_week INTEGER NOT NULL,
  expires_season INTEGER NOT NULL,
  expires_week INTEGER NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('ACTIVE','EXPIRED','ACCEPTED','REJECTED')),
  created_at TEXT NOT NULL,
  UNIQUE(club_id,generation)
);
CREATE TABLE IF NOT EXISTS sponsor_offers(
  offer_id INTEGER PRIMARY KEY AUTOINCREMENT,
  offer_set_id INTEGER NOT NULL,
  sponsor_id INTEGER NOT NULL,
  star_rating INTEGER NOT NULL CHECK(star_rating BETWEEN 1 AND 5),
  minimum_overall REAL NOT NULL,
  upfront_payment INTEGER NOT NULL,
  weekly_payment INTEGER NOT NULL,
  mission_bonus INTEGER NOT NULL,
  contract_weeks INTEGER NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('PENDING','ACCEPTED','EXPIRED','REJECTED')),
  accepted_at TEXT,
  FOREIGN KEY(offer_set_id) REFERENCES sponsor_offer_sets(offer_set_id),
  FOREIGN KEY(sponsor_id) REFERENCES sponsor_templates(sponsor_id)
);
CREATE TABLE IF NOT EXISTS sponsor_contracts(
  contract_id INTEGER PRIMARY KEY AUTOINCREMENT,
  club_id INTEGER NOT NULL,
  offer_id INTEGER NOT NULL UNIQUE,
  sponsor_id INTEGER NOT NULL,
  star_rating INTEGER NOT NULL,
  upfront_payment INTEGER NOT NULL,
  weekly_payment INTEGER NOT NULL,
  mission_bonus INTEGER NOT NULL,
  start_season INTEGER NOT NULL,
  start_week INTEGER NOT NULL,
  end_season INTEGER NOT NULL,
  end_week INTEGER NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('ACTIVE','EXPIRED','TERMINATED')),
  created_at TEXT NOT NULL,
  FOREIGN KEY(offer_id) REFERENCES sponsor_offers(offer_id),
  FOREIGN KEY(sponsor_id) REFERENCES sponsor_templates(sponsor_id)
);
CREATE TABLE IF NOT EXISTS sponsor_missions(
  mission_id INTEGER PRIMARY KEY AUTOINCREMENT,
  contract_id INTEGER NOT NULL,
  club_id INTEGER NOT NULL,
  mission_type TEXT NOT NULL,
  title TEXT NOT NULL,
  target_value REAL NOT NULL,
  current_value REAL NOT NULL DEFAULT 0,
  reward INTEGER NOT NULL,
  start_season INTEGER NOT NULL,
  start_week INTEGER NOT NULL,
  deadline_season INTEGER NOT NULL,
  deadline_week INTEGER NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('ACTIVE','COMPLETED','FAILED')),
  completed_at TEXT,
  FOREIGN KEY(contract_id) REFERENCES sponsor_contracts(contract_id)
);
CREATE TABLE IF NOT EXISTS sponsor_weekly_runs(
  club_id INTEGER NOT NULL,
  season INTEGER NOT NULL,
  week INTEGER NOT NULL,
  processed_at TEXT NOT NULL,
  PRIMARY KEY(club_id,season,week)
);
CREATE TABLE IF NOT EXISTS sponsor_mission_event_progress(
  mission_id INTEGER NOT NULL,
  event_type TEXT NOT NULL,
  event_id TEXT NOT NULL,
  delta REAL NOT NULL,
  processed_at TEXT NOT NULL,
  PRIMARY KEY(mission_id,event_type,event_id)
);
"""


@dataclass(frozen=True)
class SponsorshipProfile:
    club_id: int
    overall_score: float
    sponsor_stars: int


class SponsorshipService:
    def __init__(self, db: str | Path | sqlite3.Connection):
        assert_mutable_state_path(db) if not isinstance(db, sqlite3.Connection) else None
        self.connection = sqlite3.connect(str(db)) if not isinstance(db, sqlite3.Connection) else db
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.executescript(SCHEMA)
        self.clock = LogicalClock(self.connection)
        self.ledger = FinanceLedger(self.connection)
        self.events = ClubEventService(self.connection)
        self.connection.commit()

    def close(self):
        self.connection.close()

    def _absolute_week(self, season: int, week: int) -> int:
        return int(season) * 52 + int(week) - 1

    def _season_week(self, absolute_week: int) -> tuple[int, int]:
        season, week_offset = divmod(absolute_week, 52)
        return season, week_offset + 1

    def _context(self, action: str, source_id: str) -> WorldTickContext:
        current = self.clock.current()
        from datetime import date
        return WorldTickContext(
            tick_id=f"sponsorship:{action}:{source_id}:{current['current_season']}:{current['current_week']}",
            current_date=date.fromisoformat(current["current_date"]),
            season=int(current["current_season"]),
            week=int(current["current_week"]),
            month=int(current["current_month"]),
            advance_type="week",
        )

    def _current_profile(self, club_id: int, refresh: bool, managed_transaction: bool = True) -> SponsorshipProfile:
        if refresh:
            profile = InstitutionalPowerService(self.connection).refresh(club_id, managed_transaction=managed_transaction)
        else:
            profile = InstitutionalPowerService(self.connection).get(club_id)
            if profile is None:
                raise DomainError(DomainErrorCode.INSTITUTIONAL_PROFILE_NOT_INITIALIZED)
        return SponsorshipProfile(club_id, profile.overall_score, profile.sponsor_stars)

    def seed_templates(self, managed_transaction: bool = True) -> int:
        now = self.clock.current()["current_date"]
        created = 0
        with (self.connection if managed_transaction else nullcontext()):
            for code, name, industry, stars in SPONSOR_TEMPLATES:
                cursor = self.connection.execute(
                    """INSERT OR IGNORE INTO sponsor_templates(code,name,industry,base_stars,generation_version,created_at)
                       VALUES(?,?,?,?,?,?)""",
                    (code, name, industry, stars, FORMULA_VERSION, now),
                )
                created += cursor.rowcount
        return created

    def _active_contract(self, club_id: int) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT * FROM sponsor_contracts WHERE club_id=? AND status='ACTIVE' ORDER BY contract_id DESC LIMIT 1",
            (club_id,),
        ).fetchone()

    def _active_offer_set(self, club_id: int) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT * FROM sponsor_offer_sets WHERE club_id=? AND status='ACTIVE' ORDER BY generation DESC LIMIT 1",
            (club_id,),
        ).fetchone()

    def _expire_due(self, club_id: int, managed_transaction: bool = True) -> None:
        current = self.clock.current()
        current_week = self._absolute_week(current["current_season"], current["current_week"])
        with (self.connection if managed_transaction else nullcontext()):
            stale_sets = self.connection.execute(
                "SELECT offer_set_id FROM sponsor_offer_sets WHERE club_id=? AND status='ACTIVE'", (club_id,)
            ).fetchall()
            for row in stale_sets:
                offer_set = self.connection.execute(
                    "SELECT expires_season,expires_week FROM sponsor_offer_sets WHERE offer_set_id=?", (row["offer_set_id"],)
                ).fetchone()
                if current_week > self._absolute_week(offer_set["expires_season"], offer_set["expires_week"]):
                    self.connection.execute("UPDATE sponsor_offer_sets SET status='EXPIRED' WHERE offer_set_id=?", (row["offer_set_id"],))
                    self.connection.execute("UPDATE sponsor_offers SET status='EXPIRED' WHERE offer_set_id=? AND status='PENDING'", (row["offer_set_id"],))
            contracts = self.connection.execute(
                "SELECT contract_id,end_season,end_week FROM sponsor_contracts WHERE club_id=? AND status='ACTIVE'", (club_id,)
            ).fetchall()
            for contract in contracts:
                if current_week > self._absolute_week(contract["end_season"], contract["end_week"]):
                    self.connection.execute("UPDATE sponsor_contracts SET status='EXPIRED' WHERE contract_id=?", (contract["contract_id"],))

    def _eligible_star(self, overall: float) -> int:
        return max(star for star, rule in STAR_RULES.items() if overall >= rule["minimum_overall"])

    def _generate_offer_set(self, club_id: int, managed_transaction: bool = True) -> list[dict]:
        self.seed_templates(managed_transaction)
        self._expire_due(club_id, managed_transaction)
        if self._active_contract(club_id):
            return []
        active = self._active_offer_set(club_id)
        if active:
            return self._offers_for_set(int(active["offer_set_id"]))
        profile = self._current_profile(club_id, refresh=managed_transaction, managed_transaction=managed_transaction)
        current = self.clock.current()
        next_generation = int(self.connection.execute(
            "SELECT COALESCE(MAX(generation),0)+1 AS value FROM sponsor_offer_sets WHERE club_id=?", (club_id,)
        ).fetchone()["value"])
        expires_absolute = self._absolute_week(current["current_season"], current["current_week"]) + OFFER_WINDOW_WEEKS - 1
        expires_season, expires_week = self._season_week(expires_absolute)
        now = current["current_date"]
        templates = self.connection.execute("SELECT * FROM sponsor_templates ORDER BY sponsor_id").fetchall()
        eligible_max = self._eligible_star(profile.overall_score)
        rng = Random(f"{club_id}:{next_generation}:{FORMULA_VERSION}")
        with (self.connection if managed_transaction else nullcontext()):
            cursor = self.connection.execute(
                """INSERT INTO sponsor_offer_sets(club_id,generation,source_overall,source_stars,created_season,created_week,
                   expires_season,expires_week,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (club_id, next_generation, profile.overall_score, profile.sponsor_stars, current["current_season"], current["current_week"],
                 expires_season, expires_week, "ACTIVE", now),
            )
            offer_set_id = int(cursor.lastrowid)
            deltas = (-1, 0, 1)
            used_sponsor_ids: set[int] = set()
            for index in range(OFFERS_PER_WINDOW):
                requested_star = max(1, min(eligible_max, profile.sponsor_stars + deltas[index] + rng.choice((-1, 0, 0, 1))))
                matching = [template for template in templates if int(template["base_stars"]) == requested_star and int(template["sponsor_id"]) not in used_sponsor_ids]
                if not matching:
                    matching = [template for template in templates if int(template["base_stars"]) == requested_star]
                sponsor = rng.choice(matching)
                used_sponsor_ids.add(int(sponsor["sponsor_id"]))
                rule = STAR_RULES[requested_star]
                variability = 0.90 + rng.random() * 0.20
                self.connection.execute(
                    """INSERT INTO sponsor_offers(offer_set_id,sponsor_id,star_rating,minimum_overall,upfront_payment,weekly_payment,
                       mission_bonus,contract_weeks,status) VALUES(?,?,?,?,?,?,?,?,?)""",
                    (offer_set_id, sponsor["sponsor_id"], requested_star, rule["minimum_overall"],
                     round(rule["upfront"] * variability), round(rule["weekly"] * variability),
                     round(rule["mission"] * variability), CONTRACT_WEEKS, "PENDING"),
                )
        return self._offers_for_set(offer_set_id)

    def _offers_for_set(self, offer_set_id: int) -> list[dict]:
        rows = self.connection.execute(
            """SELECT offer.offer_id,offer.star_rating,offer.minimum_overall,offer.upfront_payment,offer.weekly_payment,
                      offer.mission_bonus,offer.contract_weeks,offer.status,template.name,template.industry,
                      offers.expires_season,offers.expires_week,offers.source_overall,offers.source_stars
               FROM sponsor_offers offer
               JOIN sponsor_offer_sets offers ON offers.offer_set_id=offer.offer_set_id
               JOIN sponsor_templates template ON template.sponsor_id=offer.sponsor_id
               WHERE offer.offer_set_id=? ORDER BY offer.star_rating DESC,offer.offer_id""",
            (offer_set_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def bootstrap_club(self, club_id: int) -> dict:
        StaffMarketService(self.connection).ensure_club_economy(club_id)
        self.seed_templates()
        offers = self._generate_offer_set(club_id)
        profile = self._current_profile(club_id, refresh=False)
        return {"club_id": club_id, "overall_score": profile.overall_score, "sponsor_stars": profile.sponsor_stars, "offers": offers}

    def bootstrap_all_clubs(self) -> dict:
        self.seed_templates()
        club_ids = [int(row["club_id"]) for row in self.connection.execute("SELECT club_id FROM club_payroll_profiles ORDER BY club_id").fetchall()]
        created = 0
        skipped = 0
        for club_id in club_ids:
            before = self._active_offer_set(club_id) or self._active_contract(club_id)
            self.bootstrap_club(club_id)
            if before:
                skipped += 1
            else:
                created += 1
        return {"clubs_total": len(club_ids), "created": created, "skipped": skipped, "formula_version": FORMULA_VERSION}

    def offers(self, club_id: int) -> list[dict]:
        active = self._active_offer_set(club_id)
        return self._offers_for_set(int(active["offer_set_id"])) if active else []

    def _mission_definition(self, club_id: int, contract: sqlite3.Row) -> tuple[str, str, float]:
        profile = self._current_profile(club_id, refresh=False)
        mission_type = MISSION_TYPES[int(contract["contract_id"]) % len(MISSION_TYPES)]
        if mission_type == "ct_quality":
            target = min(100.0, profile.overall_score + 5 + int(contract["star_rating"]) * 2)
            return mission_type, "Eleve a qualidade institucional do CT", target
        if mission_type == "squad_quality":
            target = min(100.0, profile.overall_score + 3 + int(contract["star_rating"]))
            return mission_type, "Fortaleça o núcleo esportivo do clube", target
        if mission_type == "match_wins":
            return mission_type, "Conquiste vitórias em partidas oficiais", float(1 + int(contract["star_rating"]))
        if mission_type == "goals_scored":
            return mission_type, "Marque gols em partidas oficiais", float(2 + int(contract["star_rating"]) * 2)
        if mission_type == "match_attendance":
            return mission_type, "Alcance público nos jogos como mandante", float(8_000 + int(contract["star_rating"]) * 4_000)
        target = min(100.0, profile.overall_score + 2 + int(contract["star_rating"]))
        return mission_type, "Amplie o overall institucional", target

    def _mission_value(self, club_id: int, mission_type: str, managed_transaction: bool = True) -> float:
        if mission_type in {"match_wins", "goals_scored", "match_attendance"}:
            return 0.0
        profile = InstitutionalPowerService(self.connection).refresh(club_id, managed_transaction=managed_transaction)
        if mission_type == "ct_quality":
            return profile.ct_score
        if mission_type == "squad_quality":
            return profile.squad_score
        return profile.overall_score

    def _complete_mission(self, mission: sqlite3.Row, context: WorldTickContext, managed_transaction: bool = True) -> int | None:
        if mission["status"] != "ACTIVE":
            return None
        cursor = self.connection.execute("UPDATE sponsor_missions SET status='COMPLETED',completed_at=? WHERE mission_id=? AND status='ACTIVE'", (context.current_date.isoformat(), mission["mission_id"]))
        if not cursor.rowcount:
            return None
        reward = int(mission["reward"])
        self.connection.execute(
            "UPDATE club_economic_state SET cash=cash+?,budget=budget+?,revenue_accumulated=revenue_accumulated+?,updated_at=? WHERE club_id=?",
            (reward, reward, reward, context.current_date.isoformat(), mission["club_id"]),
        )
        self.ledger.post(context, int(mission["club_id"]), "INCOME", "SPONSOR_MISSION", reward, "sponsorship_mission", str(mission["mission_id"]), mission["title"])
        self.events.record(
            int(mission["club_id"]),
            "PATROCINIO",
            "HIGH",
            "Missão de patrocínio concluída",
            f"A missão ‘{mission['title']}’ liberou R$ {reward:,} em receita contratual.",
            f"event:sponsor-mission:{mission['mission_id']}",
            origin="sponsorship_service",
            event_date=context.current_date,
            impact="SPONSOR_MISSION_REWARD",
            managed_transaction=managed_transaction,
        )
        return reward

    def _record_match_progress_values(self, club_id: int, match_id: int, goals_for: int, goals_against: int, attendance: int | None, context: WorldTickContext, managed_transaction: bool = True) -> dict:
        """Aplica valores já validados do estado persistido."""
        completed: list[int] = []
        updated = 0
        missions = self.connection.execute("SELECT * FROM sponsor_missions WHERE club_id=? AND status='ACTIVE' AND mission_type IN ('match_wins','goals_scored','match_attendance')", (club_id,)).fetchall()
        for mission in missions:
            delta = 0.0
            event_type = "match"
            if mission["mission_type"] == "match_wins":
                delta = 1.0 if goals_for > goals_against else 0.0
            elif mission["mission_type"] == "goals_scored":
                delta = float(max(0, goals_for))
            elif mission["mission_type"] == "match_attendance" and attendance is not None:
                delta = float(max(0, attendance))
                event_type = "attendance"
            if delta <= 0:
                continue
            with (self.connection if managed_transaction else nullcontext()):
                cursor = self.connection.execute("INSERT OR IGNORE INTO sponsor_mission_event_progress(mission_id,event_type,event_id,delta,processed_at) VALUES(?,?,?,?,?)", (mission["mission_id"], event_type, str(match_id), delta, context.current_date.isoformat()))
                if not cursor.rowcount:
                    continue
                current = min(float(mission["target_value"]), float(mission["current_value"]) + delta)
                self.connection.execute("UPDATE sponsor_missions SET current_value=? WHERE mission_id=?", (current, mission["mission_id"]))
                refreshed = self.connection.execute("SELECT * FROM sponsor_missions WHERE mission_id=?", (mission["mission_id"],)).fetchone()
                if current >= float(refreshed["target_value"]):
                    reward = self._complete_mission(refreshed, context, managed_transaction=managed_transaction)
                    if reward is not None:
                        completed.append(reward)
                updated += 1
        return {"updated": updated, "completed_rewards": completed}

    def record_match_progress_from_state(self, match_id: int, context: WorldTickContext | None = None, managed_transaction: bool = True) -> dict:
        """Atualiza missões somente a partir de uma partida real e de sua bilheteria já persistida."""
        exists = self.connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='matches'").fetchone()
        if not exists:
            raise DomainError(DomainErrorCode.MATCH_NOT_FOUND)
        match = self.connection.execute("SELECT * FROM matches WHERE match_id=?", (match_id,)).fetchone()
        if not match:
            raise DomainError(DomainErrorCode.MATCH_NOT_FOUND)
        if match["status"] != "PLAYED":
            raise DomainError(DomainErrorCode.MATCH_NOT_PLAYED)
        context = context or self._context("match", str(match_id))
        attendance = self.connection.execute("SELECT actual_attendance FROM attendance_records WHERE match_id=?", (match_id,)).fetchone()
        home = self._record_match_progress_values(int(match["home_club_id"]), match_id, int(match["home_goals"]), int(match["away_goals"]), int(attendance["actual_attendance"]) if attendance else None, context, managed_transaction)
        away = self._record_match_progress_values(int(match["away_club_id"]), match_id, int(match["away_goals"]), int(match["home_goals"]), None, context, managed_transaction)
        return {"match_id": match_id, "home": home, "away": away, "attendance_available": attendance is not None}

    def accept_offer(self, club_id: int, offer_id: int) -> dict:
        self._expire_due(club_id)
        offer = self.connection.execute(
            """SELECT offer.*,offers.club_id,offers.status AS offer_set_status,template.name,template.industry
               FROM sponsor_offers offer JOIN sponsor_offer_sets offers ON offers.offer_set_id=offer.offer_set_id
               JOIN sponsor_templates template ON template.sponsor_id=offer.sponsor_id WHERE offer.offer_id=?""",
            (offer_id,),
        ).fetchone()
        if offer is None:
            raise DomainError(DomainErrorCode.SPONSOR_OFFER_NOT_FOUND)
        if int(offer["club_id"]) != club_id or offer["status"] != "PENDING" or offer["offer_set_status"] != "ACTIVE":
            raise DomainError(DomainErrorCode.SPONSOR_OFFER_UNAVAILABLE)
        if self._active_contract(club_id):
            raise DomainError(DomainErrorCode.SPONSOR_CONTRACT_ACTIVE)
        profile = self._current_profile(club_id, refresh=True)
        if profile.overall_score < float(offer["minimum_overall"]):
            raise DomainError(DomainErrorCode.SPONSOR_REQUIREMENT_NOT_MET)
        current = self.clock.current()
        end_season, end_week = self._season_week(self._absolute_week(current["current_season"], current["current_week"]) + int(offer["contract_weeks"]) - 1)
        context = self._context("accept", str(offer_id))
        with self.connection:
            self.connection.execute(
                """INSERT INTO sponsor_contracts(club_id,offer_id,sponsor_id,star_rating,upfront_payment,weekly_payment,mission_bonus,
                   start_season,start_week,end_season,end_week,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (club_id, offer_id, offer["sponsor_id"], offer["star_rating"], offer["upfront_payment"], offer["weekly_payment"],
                 offer["mission_bonus"], current["current_season"], current["current_week"], end_season, end_week, "ACTIVE", current["current_date"]),
            )
            contract_id = int(self.connection.execute("SELECT last_insert_rowid() AS id").fetchone()["id"])
            self.connection.execute("UPDATE sponsor_offers SET status='ACCEPTED',accepted_at=? WHERE offer_id=?", (current["current_date"], offer_id))
            self.connection.execute("UPDATE sponsor_offers SET status='REJECTED' WHERE offer_set_id=? AND offer_id<>? AND status='PENDING'", (offer["offer_set_id"], offer_id))
            self.connection.execute("UPDATE sponsor_offer_sets SET status='ACCEPTED' WHERE offer_set_id=?", (offer["offer_set_id"],))
            self.connection.execute(
                "UPDATE club_economic_state SET cash=cash+?,budget=budget+?,revenue_accumulated=revenue_accumulated+?,updated_at=? WHERE club_id=?",
                (offer["upfront_payment"], offer["upfront_payment"], offer["upfront_payment"], current["current_date"], club_id),
            )
            self.ledger.post(context, club_id, "INCOME", "SPONSOR_UPFRONT", int(offer["upfront_payment"]), "sponsorship_contract", str(contract_id), f"Sinal de {offer['name']}")
            contract = self.connection.execute("SELECT * FROM sponsor_contracts WHERE contract_id=?", (contract_id,)).fetchone()
            mission_type, title, target = self._mission_definition(club_id, contract)
            self.connection.execute(
                """INSERT INTO sponsor_missions(contract_id,club_id,mission_type,title,target_value,current_value,reward,start_season,start_week,
                   deadline_season,deadline_week,status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (contract_id, club_id, mission_type, title, target, self._mission_value(club_id, mission_type), offer["mission_bonus"],
                 current["current_season"], current["current_week"], end_season, end_week, "ACTIVE"),
            )
            self.events.record(
                club_id,
                "PATROCINIO",
                "NORMAL",
                f"Contrato firmado com {offer['name']}",
                f"O sinal de R$ {int(offer['upfront_payment']):,} e a receita semanal foram registrados no caixa.",
                f"event:sponsor-contract:{contract_id}",
                origin="sponsorship_service",
                event_date=current["current_date"],
                impact="SPONSOR_CONTRACT_ACCEPTED",
                managed_transaction=False,
            )
        return {"contract_id": contract_id, "sponsor": offer["name"], "star_rating": int(offer["star_rating"]), "upfront_payment": int(offer["upfront_payment"]), "weekly_payment": int(offer["weekly_payment"]), "end_season": end_season, "end_week": end_week}

    def _evaluate_missions(self, club_id: int, context: WorldTickContext, managed_transaction: bool = True) -> list[int]:
        rewards: list[int] = []
        missions = self.connection.execute(
            "SELECT * FROM sponsor_missions WHERE club_id=? AND status='ACTIVE' ORDER BY mission_id", (club_id,)
        ).fetchall()
        now_abs = self._absolute_week(context.season, context.week)
        for mission in missions:
            current_value = float(mission["current_value"]) if mission["mission_type"] in {"match_wins", "goals_scored", "match_attendance"} else self._mission_value(club_id, mission["mission_type"], managed_transaction=managed_transaction)
            deadline_abs = self._absolute_week(mission["deadline_season"], mission["deadline_week"])
            with (self.connection if managed_transaction else nullcontext()):
                self.connection.execute("UPDATE sponsor_missions SET current_value=? WHERE mission_id=?", (current_value, mission["mission_id"]))
                if current_value >= float(mission["target_value"]):
                    refreshed = self.connection.execute("SELECT * FROM sponsor_missions WHERE mission_id=?", (mission["mission_id"],)).fetchone()
                    reward = self._complete_mission(refreshed, context, managed_transaction=managed_transaction)
                    if reward is not None:
                        rewards.append(reward)
                elif now_abs > deadline_abs:
                    self.connection.execute("UPDATE sponsor_missions SET status='FAILED' WHERE mission_id=?", (mission["mission_id"],))
        return rewards

    def process_week(self, club_id: int, managed_transaction: bool = True) -> dict:
        current = self.clock.current()
        existing = self.connection.execute(
            "SELECT 1 FROM sponsor_weekly_runs WHERE club_id=? AND season=? AND week=?", (club_id, current["current_season"], current["current_week"]),
        ).fetchone()
        if existing:
            return {"processed": False, "reason": "ALREADY_PROCESSED", "weekly_income": 0, "mission_rewards": []}
        self._expire_due(club_id, managed_transaction)
        context = self._context("weekly", str(club_id))
        weekly_income = 0
        active = self._active_contract(club_id)
        with (self.connection if managed_transaction else nullcontext()):
            if active is not None:
                weekly_income = int(active["weekly_payment"])
                self.connection.execute(
                    "UPDATE club_economic_state SET cash=cash+?,budget=budget+?,revenue_accumulated=revenue_accumulated+?,updated_at=? WHERE club_id=?",
                    (weekly_income, weekly_income, weekly_income, context.current_date.isoformat(), club_id),
                )
                self.ledger.post(context, club_id, "INCOME", "SPONSOR_WEEKLY", weekly_income, "sponsorship_contract", str(active["contract_id"]), "Receita semanal de patrocínio")
            mission_rewards = self._evaluate_missions(club_id, context, managed_transaction)
            self.connection.execute("INSERT INTO sponsor_weekly_runs VALUES(?,?,?,?)", (club_id, context.season, context.week, context.current_date.isoformat()))
        self._expire_due(club_id, managed_transaction)
        generated = self._generate_offer_set(club_id, managed_transaction)
        return {"processed": True, "weekly_income": weekly_income, "mission_rewards": mission_rewards, "new_offers": len(generated)}

    def process_week_all(self, managed_transaction: bool = True) -> dict:
        club_ids = [int(row["club_id"]) for row in self.connection.execute("SELECT club_id FROM club_payroll_profiles ORDER BY club_id").fetchall()]
        processed = 0
        already_processed = 0
        for club_id in club_ids:
            result = self.process_week(club_id, managed_transaction)
            if result["processed"]:
                processed += 1
            else:
                already_processed += 1
        return {"clubs_total": len(club_ids), "processed": processed, "already_processed": already_processed}

    def summary(self, club_id: int) -> dict:
        profile = self._current_profile(club_id, refresh=False)
        institutional = InstitutionalPowerService(self.connection).get(club_id)
        active = self.connection.execute(
            """SELECT contract.*,template.name,template.industry FROM sponsor_contracts contract
               JOIN sponsor_templates template ON template.sponsor_id=contract.sponsor_id
               WHERE contract.club_id=? AND contract.status='ACTIVE' ORDER BY contract.contract_id DESC LIMIT 1""",
            (club_id,),
        ).fetchone()
        offers = self.offers(club_id)
        missions = self.connection.execute(
            "SELECT mission_id,title,mission_type,target_value,current_value,reward,status,deadline_season,deadline_week FROM sponsor_missions WHERE club_id=? ORDER BY mission_id DESC",
            (club_id,),
        ).fetchall()
        return {
            "club_id": club_id,
            "institutional_overall": profile.overall_score,
            "sponsor_stars": profile.sponsor_stars,
            "institutional_profile": {
                "squad_score": institutional.squad_score,
                "ct_score": institutional.ct_score,
                "stadium_score": institutional.stadium_score,
                "squad_available": institutional.squad_available,
                "ct_available": institutional.ct_available,
                "stadium_available": institutional.stadium_available,
            },
            "active_contract": dict(active) if active else None,
            "offers": offers,
            "missions": [dict(row) for row in missions],
        }
