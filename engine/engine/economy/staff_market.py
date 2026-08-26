from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import sqlite3
from contextlib import nullcontext

from engine.staff.state_store import SCHEMA as STAFF_SCHEMA
from engine.world.time_and_finance import FinanceLedger, LogicalClock, WorldTickContext


from engine.core.state_store import assert_mutable_state_path
from engine.core.domain_errors import DomainError, DomainErrorCode
FORMULA_VERSION = "brasfoot-adapted-weekly-v2"
INITIAL_RESERVE_WEEKS = 39
ROLE_MULTIPLIER = {"treinador": 1.35, "auxiliar": 1.0, "preparador_fisico": 1.05, "medico": 1.15, "scout": 0.95}
HIGH_TIER_COUNTRIES = frozenset({3, 65, 72, 97, 104})
DIVISION_BASE_WEEKLY = {
    "high": {1: 750, 2: 550, 3: 500, 4: 450, 5: 450},
    "standard": {1: 600, 2: 500, 3: 450, 4: 400, 5: 400},
}
POSITION_SALARY_ADJUSTMENT = {
    "Goleiro": -70,
    "Zagueiro": -30,
    "Lateral": -40,
    "Atacante": -50,
}
DEPARTMENTS = {
    "base": {"label": "Base", "purchase": 70_000, "maintenance": 2_000, "capacity": 18},
    "medicina": {"label": "Medicina", "purchase": 80_000, "maintenance": 2_400, "capacity": 10},
    "preparacao_fisica": {"label": "Preparação física", "purchase": 75_000, "maintenance": 2_200, "capacity": 14},
    "analise": {"label": "Análise", "purchase": 60_000, "maintenance": 1_800, "capacity": 12},
}
CATALOG = (
    ("Rafael Siqueira", "treinador", 46, 7, 78, 76, "tática e gestão"),
    ("Marina Tavares", "treinador", 39, 6, 70, 82, "desenvolvimento"),
    ("Diego Valente", "auxiliar", 38, 6, 72, 74, "transição ofensiva"),
    ("Camila Farias", "auxiliar", 34, 5, 66, 79, "análise de adversários"),
    ("Bruno Luz", "preparador_fisico", 42, 7, 75, 73, "resistência"),
    ("Aline Prado", "preparador_fisico", 36, 5, 64, 81, "prevenção"),
    ("Dra. Renata Moura", "medico", 44, 8, 80, 78, "medicina esportiva"),
    ("Dr. Hugo Martins", "medico", 40, 6, 69, 76, "fisioterapia"),
    ("Leandro Pires", "scout", 41, 7, 73, 75, "América do Sul"),
    ("Nina Campos", "scout", 32, 5, 62, 83, "mercados emergentes"),
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS club_economic_state(
  club_id INTEGER PRIMARY KEY,cash INTEGER NOT NULL DEFAULT 0,budget INTEGER NOT NULL DEFAULT 0,
  revenue_accumulated INTEGER NOT NULL DEFAULT 0,expense_accumulated INTEGER NOT NULL DEFAULT 0,
  debt INTEGER NOT NULL DEFAULT 0,obligations INTEGER NOT NULL DEFAULT 0,payroll INTEGER NOT NULL DEFAULT 0,
  financial_status TEXT NOT NULL DEFAULT 'HEALTHY',updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS club_payroll_profiles(
  club_id INTEGER PRIMARY KEY,formula_version TEXT NOT NULL,team_power REAL NOT NULL,country_factor REAL NOT NULL,
  base_level INTEGER NOT NULL,weekly_player_payroll INTEGER NOT NULL,weekly_staff_payroll INTEGER NOT NULL DEFAULT 0,
  weekly_department_maintenance INTEGER NOT NULL DEFAULT 0,initial_cash INTEGER NOT NULL,updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS staff_contracts(
  contract_id INTEGER PRIMARY KEY AUTOINCREMENT,staff_id INTEGER NOT NULL,club_id INTEGER NOT NULL,start_date TEXT NOT NULL,end_date TEXT NOT NULL,
  weekly_salary INTEGER NOT NULL,termination_fee INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'ACTIVE',terminated_at TEXT,
  FOREIGN KEY(staff_id) REFERENCES staff_members(staff_id)
);
CREATE TABLE IF NOT EXISTS training_history(
  history_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,event_type TEXT NOT NULL,event_date TEXT NOT NULL,payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS staff_market_catalog(
  catalog_key TEXT PRIMARY KEY,staff_id INTEGER NOT NULL UNIQUE,generation_version TEXT NOT NULL,created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS weekly_economy_runs(
  club_id INTEGER NOT NULL,season INTEGER NOT NULL,week INTEGER NOT NULL,weekly_cost INTEGER NOT NULL,
  processed_at TEXT NOT NULL,PRIMARY KEY(club_id,season,week)
);
CREATE TABLE IF NOT EXISTS club_player_payrolls(
  club_id INTEGER NOT NULL,player_id INTEGER NOT NULL,formula_version TEXT NOT NULL,
  player_strength INTEGER NOT NULL,weekly_salary INTEGER NOT NULL,updated_at TEXT NOT NULL,
  PRIMARY KEY(club_id,player_id)
);
"""


@dataclass(frozen=True)
class PayrollProfile:
    club_id: int
    team_power: float
    country_factor: float
    base_level: int
    weekly_player_payroll: int
    weekly_staff_payroll: int
    weekly_department_maintenance: int
    initial_cash: int


class StaffMarketService:
    def __init__(self, db: str | Path | sqlite3.Connection):
        assert_mutable_state_path(db) if not isinstance(db, sqlite3.Connection) else None
        self.connection = sqlite3.connect(str(db)) if not isinstance(db, sqlite3.Connection) else db
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.executescript(STAFF_SCHEMA)
        self.connection.executescript(SCHEMA)
        self.clock = LogicalClock(self.connection)
        self.ledger = FinanceLedger(self.connection)
        self._country_factor_cache: dict[int, float] = {}
        self._global_player_average: float | None = None
        self.connection.commit()

    def close(self):
        self.connection.close()

    def _context(self, action: str, source_id: str) -> WorldTickContext:
        current = self.clock.current()
        current_date = date.fromisoformat(current["current_date"])
        return WorldTickContext(
            tick_id=f"staff-market:{action}:{source_id}:{current['current_season']}:{current['current_week']}",
            current_date=current_date,
            season=int(current["current_season"]),
            week=int(current["current_week"]),
            month=int(current["current_month"]),
            advance_type="week",
        )

    def _squad_power(self, club_id: int) -> tuple[float, int]:
        row = self.connection.execute(
            """
            SELECT AVG((player.cr1 + player.cr2) / 2.0) AS average_cr,
                   AVG(CASE WHEN membership.status='Titular' THEN (player.cr1 + player.cr2) / 2.0 END) AS starter_average_cr,
                   SUM(CASE WHEN player.estrela=1 THEN 1 ELSE 0 END) AS stars,
                   SUM(CASE WHEN player.top_mundial=1 THEN 1 ELSE 0 END) AS world_class
            FROM jogador_time membership JOIN jogadores player ON player.jogador_id=membership.jogador_id
            WHERE membership.time_id=?
            """,
            (club_id,),
        ).fetchone()
        if row is None or row["average_cr"] is None:
            raise ValueError("CLUB_SQUAD_NOT_FOUND")
        core = float(row["starter_average_cr"] or row["average_cr"]) * 10
        bonus = min(12, int(row["stars"] or 0) * 1.2) + min(8, int(row["world_class"] or 0) * 2)
        return min(100.0, max(25.0, core + bonus)), int(row["stars"] or 0)

    def _country_factor(self, club_id: int) -> float:
        country = self.connection.execute("SELECT pais_id FROM times WHERE time_id=?", (club_id,)).fetchone()
        if country is None:
            raise DomainError(DomainErrorCode.CLUB_NOT_FOUND)
        country_id = int(country["pais_id"])
        if country_id in self._country_factor_cache:
            return self._country_factor_cache[country_id]
        if self._global_player_average is None:
            value = self.connection.execute(
                "SELECT AVG((player.cr1 + player.cr2) / 2.0) AS value FROM jogador_time membership JOIN jogadores player ON player.jogador_id=membership.jogador_id"
            ).fetchone()["value"]
            self._global_player_average = float(value) if value else 0.0
        country_avg = self.connection.execute(
            """
            SELECT AVG((player.cr1 + player.cr2) / 2.0) AS value
            FROM times team JOIN jogador_time membership ON membership.time_id=team.time_id
            JOIN jogadores player ON player.jogador_id=membership.jogador_id WHERE team.pais_id=?
            """,
            (country_id,),
        ).fetchone()["value"]
        if not self._global_player_average or not country_avg:
            factor = 1.0
        else:
            factor = min(1.25, max(0.80, float(country_avg) / self._global_player_average))
        self._country_factor_cache[country_id] = factor
        return factor

    def _base_level(self, club_id: int) -> int:
        row = self.connection.execute("SELECT level FROM club_departments WHERE club_id=? AND department='base'", (club_id,)).fetchone()
        return int(row["level"]) if row else 0

    def _derived_division(self, team_power: float) -> int:
        """Mapeia o poder preservado no SQL para a faixa de divisão original.

        A fonte normalizada não conserva a divisão dinâmica do executável. A
        classificação é determinística e fica isolada aqui para poder ser
        substituída por uma competição persistida quando ela existir.
        """
        if team_power >= 78:
            return 1
        if team_power >= 60:
            return 2
        if team_power >= 45:
            return 3
        if team_power >= 32:
            return 4
        return 5

    def _player_strength(self, cr1: int, cr2: int, team_power: float) -> int:
        """Proxy determinístico para a força original, que não foi serializada no SQL."""
        attribute_ratio = max(0.0, min(1.0, ((int(cr1) + int(cr2)) / 2.0) / 13.0))
        strength = round(8 + attribute_ratio * 60 + (team_power / 100.0) * 18)
        return max(10, min(100, int(strength)))

    def _weekly_player_salary(
        self,
        *,
        strength: int,
        age: int,
        position: str,
        is_star: bool,
        is_world_class: bool,
        division: int,
        country_id: int,
        base_level: int,
    ) -> int:
        tier = "high" if country_id in HIGH_TIER_COUNTRIES else "standard"
        base = DIVISION_BASE_WEEKLY[tier][division]
        if base_level > 20:
            base += 50
        base += POSITION_SALARY_ADJUSTMENT.get(position, 0)
        salary = strength * 2 * round(0.5 * base)
        if is_star or is_world_class:
            salary += strength * 250
        if age >= 32:
            salary -= (age - 32) * 300
        salary = max(500, salary)
        if is_world_class:
            salary = round(salary * 1.4)
        return int(salary)

    def _player_payroll(self, club_id: int, team_power: float, base_level: int, managed_transaction: bool = True) -> int:
        team = self.connection.execute("SELECT pais_id FROM times WHERE time_id=?", (club_id,)).fetchone()
        if team is None:
            raise DomainError(DomainErrorCode.CLUB_NOT_FOUND)
        players = self.connection.execute(
            """
            SELECT player.jogador_id,player.cr1,player.cr2,player.idade,player.posicao,
                   player.estrela,player.top_mundial
            FROM jogador_time membership
            JOIN jogadores player ON player.jogador_id=membership.jogador_id
            WHERE membership.time_id=?
            """,
            (club_id,),
        ).fetchall()
        division = self._derived_division(team_power)
        now = self.clock.current()["current_date"]
        rows: list[tuple[int, int, int]] = []
        for player in players:
            strength = self._player_strength(player["cr1"], player["cr2"], team_power)
            salary = self._weekly_player_salary(
                strength=strength,
                age=int(player["idade"]),
                position=str(player["posicao"]),
                is_star=bool(player["estrela"]),
                is_world_class=bool(player["top_mundial"]),
                division=division,
                country_id=int(team["pais_id"]),
                base_level=base_level,
            )
            rows.append((int(player["jogador_id"]), strength, salary))
        with (self.connection if managed_transaction else nullcontext()):
            self.connection.executemany(
                """INSERT INTO club_player_payrolls(club_id,player_id,formula_version,player_strength,weekly_salary,updated_at)
                   VALUES(?,?,?,?,?,?)
                   ON CONFLICT(club_id,player_id) DO UPDATE SET formula_version=excluded.formula_version,
                     player_strength=excluded.player_strength,weekly_salary=excluded.weekly_salary,updated_at=excluded.updated_at""",
                [(club_id, player_id, FORMULA_VERSION, strength, salary, now) for player_id, strength, salary in rows],
            )
            self.connection.execute(
                """DELETE FROM club_player_payrolls WHERE club_id=? AND player_id NOT IN
                   (SELECT jogador_id FROM jogador_time WHERE time_id=?)""",
                (club_id, club_id),
            )
        return sum(salary for _, _, salary in rows)

    def _staff_payroll(self, club_id: int) -> int:
        row = self.connection.execute("SELECT COALESCE(SUM(salary),0) AS total FROM staff_members WHERE club_id=? AND status='ativo'", (club_id,)).fetchone()
        return int(row["total"])

    def _department_maintenance(self, club_id: int) -> int:
        row = self.connection.execute("SELECT COALESCE(SUM(maintenance),0) AS total FROM club_departments WHERE club_id=?", (club_id,)).fetchone()
        return int(row["total"])

    def ensure_club_economy(self, club_id: int, managed_transaction: bool = True) -> PayrollProfile:
        existing = self.connection.execute("SELECT * FROM club_payroll_profiles WHERE club_id=?", (club_id,)).fetchone()
        if existing:
            return self._profile(existing)
        power, _ = self._squad_power(club_id)
        factor = self._country_factor(club_id)
        base_level = self._base_level(club_id)
        player_payroll = self._player_payroll(club_id, power, base_level, managed_transaction=managed_transaction)
        staff_payroll = self._staff_payroll(club_id)
        maintenance = self._department_maintenance(club_id)
        weekly = player_payroll + staff_payroll + maintenance
        initial_cash = weekly * INITIAL_RESERVE_WEEKS
        now = self.clock.current()["current_date"]
        with (self.connection if managed_transaction else nullcontext()):
            self.connection.execute(
                "INSERT INTO club_payroll_profiles VALUES(?,?,?,?,?,?,?,?,?,?)",
                (club_id, FORMULA_VERSION, power, factor, base_level, player_payroll, staff_payroll, maintenance, initial_cash, now),
            )
            self.connection.execute(
                "INSERT OR IGNORE INTO club_economic_state(club_id,cash,budget,payroll,updated_at) VALUES(?,?,?,?,?)",
                (club_id, initial_cash, initial_cash, player_payroll + staff_payroll, now),
            )
        return PayrollProfile(club_id, power, factor, base_level, player_payroll, staff_payroll, maintenance, initial_cash)

    def _profile(self, row: sqlite3.Row) -> PayrollProfile:
        return PayrollProfile(int(row["club_id"]), float(row["team_power"]), float(row["country_factor"]), int(row["base_level"]), int(row["weekly_player_payroll"]), int(row["weekly_staff_payroll"]), int(row["weekly_department_maintenance"]), int(row["initial_cash"]))

    def _refresh_profile(self, club_id: int, managed_transaction: bool = True) -> PayrollProfile:
        profile = self.ensure_club_economy(club_id, managed_transaction=managed_transaction)
        power, _ = self._squad_power(club_id)
        factor = self._country_factor(club_id)
        staff = self._staff_payroll(club_id)
        maintenance = self._department_maintenance(club_id)
        base_level = self._base_level(club_id)
        player_payroll = self._player_payroll(club_id, power, base_level, managed_transaction=managed_transaction)
        now = self.clock.current()["current_date"]
        with (self.connection if managed_transaction else nullcontext()):
            self.connection.execute(
                """UPDATE club_payroll_profiles SET team_power=?,country_factor=?,base_level=?,weekly_player_payroll=?,
                   weekly_staff_payroll=?,weekly_department_maintenance=?,updated_at=? WHERE club_id=?""",
                (power, factor, base_level, player_payroll, staff, maintenance, now, club_id),
            )
            self.connection.execute("UPDATE club_economic_state SET payroll=?,updated_at=? WHERE club_id=?", (player_payroll + staff, now, club_id))
        row = self.connection.execute("SELECT * FROM club_payroll_profiles WHERE club_id=?", (club_id,)).fetchone()
        return self._profile(row)

    def seed_catalog(self) -> int:
        if self.connection.execute("SELECT 1 FROM staff_market_catalog LIMIT 1").fetchone():
            return 0
        now = self.clock.current()["current_date"]
        with self.connection:
            for index, (name, role, age, level, reputation, potential, specialization) in enumerate(CATALOG, start=1):
                cursor = self.connection.execute(
                    """INSERT INTO staff_members(name,role,age,club_id,career_start_age,experience,reputation,level,potential,specialization,salary,status,created_at,retirement_age)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (name, role, age, None, age - max(1, level), min(100, max(0, (level - 1) * 15)), reputation, level, potential, specialization, 0, "disponivel", now, 67),
                )
                self.connection.execute("INSERT INTO staff_market_catalog VALUES(?,?,?,?)", (f"{role}:{index}", int(cursor.lastrowid), FORMULA_VERSION, now))
        return len(CATALOG)

    def bootstrap_club(self, club_id: int) -> dict:
        seeded = self.seed_catalog()
        profile = self.ensure_club_economy(club_id)
        state = self.connection.execute("SELECT cash,budget,payroll FROM club_economic_state WHERE club_id=?", (club_id,)).fetchone()
        return {
            "seeded_staff": seeded,
            "club_id": club_id,
            "cash": int(state["cash"]),
            "budget": int(state["budget"]),
            "payroll": int(state["payroll"]),
            "weekly_player_payroll": profile.weekly_player_payroll,
            "weekly_staff_payroll": profile.weekly_staff_payroll,
            "weekly_department_maintenance": profile.weekly_department_maintenance,
            "initial_cash": profile.initial_cash,
            "team_power": profile.team_power,
            "country_factor": profile.country_factor,
            "base_level": profile.base_level,
        }

    def bootstrap_all_clubs(self) -> dict:
        """Inicializa uma vez a economia de todos os clubes com elenco persistido.

        A operação é explícita: nenhuma consulta de interface cria estado para
        clubes que ainda não pertencem a uma carreira ativa.
        """
        seeded = self.seed_catalog()
        club_ids = [
            int(row["time_id"])
            for row in self.connection.execute(
                """SELECT team.time_id FROM times team
                   WHERE EXISTS(SELECT 1 FROM jogador_time membership WHERE membership.time_id=team.time_id)
                   ORDER BY team.time_id"""
            ).fetchall()
        ]
        created = 0
        skipped = 0
        for club_id in club_ids:
            exists = self.connection.execute(
                "SELECT 1 FROM club_payroll_profiles WHERE club_id=?", (club_id,)
            ).fetchone()
            if exists:
                skipped += 1
                continue
            self.ensure_club_economy(club_id)
            created += 1
        return {
            "seeded_staff": seeded,
            "clubs_total": len(club_ids),
            "created": created,
            "skipped": skipped,
            "formula_version": FORMULA_VERSION,
        }

    def summary(self, club_id: int) -> dict:
        profile = self.ensure_club_economy(club_id)
        state = self.connection.execute("SELECT cash,budget,payroll,expense_accumulated FROM club_economic_state WHERE club_id=?", (club_id,)).fetchone()
        return {
            "club_id": club_id,
            "cash": int(state["cash"]),
            "budget": int(state["budget"]),
            "payroll": int(state["payroll"]),
            "expense_accumulated": int(state["expense_accumulated"]),
            "weekly_player_payroll": profile.weekly_player_payroll,
            "weekly_staff_payroll": profile.weekly_staff_payroll,
            "weekly_department_maintenance": profile.weekly_department_maintenance,
            "weekly_total": profile.weekly_player_payroll + profile.weekly_staff_payroll + profile.weekly_department_maintenance,
            "initial_cash": profile.initial_cash,
            "team_power": profile.team_power,
            "country_factor": profile.country_factor,
            "base_level": profile.base_level,
        }

    def weekly_staff_salary(self, club_id: int, staff_id: int) -> int:
        profile = self.ensure_club_economy(club_id)
        staff = self.connection.execute("SELECT role,level,reputation,potential FROM staff_members WHERE staff_id=?", (staff_id,)).fetchone()
        if staff is None:
            raise ValueError("STAFF_NOT_FOUND")
        multiplier = ROLE_MULTIPLIER.get(staff["role"], 1.0)
        raw = 900 + profile.team_power * 18 + int(staff["level"]) * 420 + int(staff["reputation"]) * 9 + int(staff["potential"]) * 4
        return int(round(raw * profile.country_factor * multiplier))

    def available_staff(self, club_id: int, role: str | None = None, min_level: int | None = None, max_level: int | None = None) -> list[dict]:
        self.seed_catalog()
        self.ensure_club_economy(club_id)
        query = "SELECT staff_id,name,role,age,experience,reputation,level,potential,specialization FROM staff_members WHERE status='disponivel'"
        args: list[object] = []
        if role:
            query += " AND role=?"; args.append(role)
        if min_level is not None:
            query += " AND level>=?"; args.append(max(1, int(min_level)))
        if max_level is not None:
            query += " AND level<=?"; args.append(min(10, int(max_level)))
        rows = self.connection.execute(query, args).fetchall()
        catalog=[]
        for row in rows:
            item={**dict(row), "weekly_salary": self.weekly_staff_salary(club_id, int(row["staff_id"]))}
            item["cost_benefit"] = round((int(row["level"])*0.4 + int(row["reputation"])*0.35 + int(row["potential"])*0.25) / max(1, item["weekly_salary"]), 6)
            catalog.append(item)
        return sorted(catalog, key=lambda item: (-item["cost_benefit"], -item["level"], -item["reputation"], item["name"]))

    def hire_staff(self, club_id: int, staff_id: int) -> dict:
        self.seed_catalog()
        profile = self.ensure_club_economy(club_id)
        staff = self.connection.execute("SELECT * FROM staff_members WHERE staff_id=?", (staff_id,)).fetchone()
        if staff is None:
            raise ValueError("STAFF_NOT_FOUND")
        if staff["status"] != "disponivel" or staff["club_id"] is not None:
            raise ValueError("STAFF_UNAVAILABLE")
        power, _ = self._squad_power(club_id)
        factor = self._country_factor(club_id)
        base_level = self._base_level(club_id)
        player_payroll = self._player_payroll(club_id, power, base_level)
        salary = self.weekly_staff_salary(club_id, staff_id)
        staff_payroll = self._staff_payroll(club_id) + salary
        now = self.clock.current()["current_date"]
        with self.connection:
            self.connection.execute("INSERT INTO staff_contracts(staff_id,club_id,start_date,end_date,weekly_salary,termination_fee,status) VALUES(?,?,?,?,?,?,?)", (staff_id, club_id, now, (date.fromisoformat(now) + timedelta(weeks=52)).isoformat(), salary, salary * 4, 'ACTIVE'))
            contract_id = int(self.connection.execute("SELECT last_insert_rowid()").fetchone()[0])
            self.connection.execute("UPDATE staff_members SET club_id=?,salary=?,contract_id=?,status='ativo' WHERE staff_id=?", (club_id, salary, contract_id, staff_id))
            self.connection.execute("INSERT INTO staff_history(staff_id,event_type,event_date,payload) VALUES(?,?,?,?)", (staff_id, "STAFF_HIRED", now, f'{{"club_id":{club_id},"weekly_salary":{salary},"contract_id":{contract_id},"end_date":"{(date.fromisoformat(now) + timedelta(weeks=52)).isoformat()}"}}'))
            self.connection.execute(
                """UPDATE club_payroll_profiles SET team_power=?,country_factor=?,base_level=?,weekly_player_payroll=?,
                   weekly_staff_payroll=?,updated_at=? WHERE club_id=?""",
                (power, factor, base_level, player_payroll, staff_payroll, now, club_id),
            )
            self.connection.execute(
                "UPDATE club_economic_state SET payroll=?,updated_at=? WHERE club_id=?",
                (player_payroll + staff_payroll, now, club_id),
            )
        return {"staff_id": staff_id, "name": staff["name"], "role": staff["role"], "weekly_salary": salary, "payroll": player_payroll + staff_payroll, "contract_id": contract_id, "end_date": (date.fromisoformat(now) + timedelta(weeks=52)).isoformat(), "termination_fee": salary * 4}

    def staff_contract(self, club_id: int, staff_id: int) -> dict:
        row = self.connection.execute("SELECT * FROM staff_contracts WHERE club_id=? AND staff_id=? AND status='ACTIVE' ORDER BY contract_id DESC LIMIT 1", (club_id, staff_id)).fetchone()
        if row is None: raise ValueError("STAFF_CONTRACT_NOT_FOUND")
        return dict(row)

    def terminate_staff(self, club_id: int, staff_id: int, waive_fee: bool = False) -> dict:
        staff = self.connection.execute("SELECT name,salary,status FROM staff_members WHERE staff_id=? AND club_id=?", (staff_id, club_id)).fetchone()
        if staff is None or staff["status"] != "ativo": raise ValueError("STAFF_NOT_ACTIVE")
        contract = self.staff_contract(club_id, staff_id)
        fee = 0 if waive_fee else int(contract["termination_fee"])
        state = self.connection.execute("SELECT cash FROM club_economic_state WHERE club_id=?", (club_id,)).fetchone()
        if state is None or int(state["cash"]) < fee: raise DomainError(DomainErrorCode.INSUFFICIENT_CASH)
        now = self.clock.current()["current_date"]
        with self.connection:
            if fee: self.connection.execute("UPDATE club_economic_state SET cash=cash-?,expense_accumulated=expense_accumulated+?,updated_at=? WHERE club_id=?", (fee, fee, now, club_id))
            self.connection.execute("UPDATE staff_contracts SET status='TERMINATED',terminated_at=? WHERE contract_id=?", (now, contract["contract_id"]))
            self.connection.execute("UPDATE staff_members SET club_id=NULL,contract_id=NULL,salary=0,status='disponivel' WHERE staff_id=?", (staff_id,))
            self.connection.execute("INSERT INTO staff_history(staff_id,event_type,event_date,payload) VALUES(?,?,?,?)", (staff_id, "STAFF_TERMINATED", now, f'{{"club_id":{club_id},"termination_fee":{fee}}}'))
        profile = self._refresh_profile(club_id)
        return {"staff_id": int(staff_id), "name": staff["name"], "termination_fee": fee, "weekly_staff_payroll": profile.weekly_staff_payroll, "status": "disponivel"}

    def replace_staff(self, club_id: int, outgoing_staff_id: int, incoming_staff_id: int) -> dict:
        if int(outgoing_staff_id) == int(incoming_staff_id): raise ValueError("STAFF_REPLACEMENT_INVALID")
        result = self.terminate_staff(club_id, outgoing_staff_id)
        hired = self.hire_staff(club_id, incoming_staff_id)
        return {"terminated": result, "hired": hired}

    def department_offer(self, club_id: int, department: str) -> dict:
        if department not in DEPARTMENTS:
            raise ValueError("DEPARTMENT_INVALID")
        profile = self.ensure_club_economy(club_id)
        existing = self.connection.execute("SELECT level FROM club_departments WHERE club_id=? AND department=?", (club_id, department)).fetchone()
        target_level = int(existing["level"]) + 1 if existing else 1
        if target_level > 10:
            raise ValueError("DEPARTMENT_MAX_LEVEL")
        rule = DEPARTMENTS[department]
        cost = int(round(rule["purchase"] * target_level * (1 + profile.team_power / 100) * profile.country_factor))
        maintenance = int(round(rule["maintenance"] * target_level * profile.country_factor))
        return {"department": department, "label": rule["label"], "target_level": target_level, "cost": cost, "maintenance": maintenance, "capacity": rule["capacity"] * target_level}

    def upgrade_department(self, club_id: int, department: str) -> dict:
        offer = self.department_offer(club_id, department)
        state = self.connection.execute("SELECT cash FROM club_economic_state WHERE club_id=?", (club_id,)).fetchone()
        if state is None or int(state["cash"]) < offer["cost"]:
            raise DomainError(DomainErrorCode.INSUFFICIENT_CASH)
        context = self._context("department", f"{club_id}:{department}:{offer['target_level']}")
        with self.connection:
            self.connection.execute("UPDATE club_economic_state SET cash=cash-?,expense_accumulated=expense_accumulated+?,updated_at=? WHERE club_id=?", (offer["cost"], offer["cost"], context.current_date.isoformat(), club_id))
            self.connection.execute(
                """INSERT INTO club_departments(club_id,department,level,cost,capacity,maintenance,efficiency) VALUES(?,?,?,?,?,?,?)
                ON CONFLICT(club_id,department) DO UPDATE SET level=excluded.level,cost=excluded.cost,capacity=excluded.capacity,maintenance=excluded.maintenance,efficiency=excluded.efficiency""",
                (club_id, department, offer["target_level"], offer["cost"], offer["capacity"], offer["maintenance"], offer["target_level"] / 10),
            )
            self.ledger.post(context, club_id, "EXPENSE", "DEPARTMENT", -offer["cost"], "department", f"{department}:{offer['target_level']}", f"{offer['label']} nível {offer['target_level']}")
            self.connection.execute("INSERT INTO training_history(club_id,event_type,event_date,payload) VALUES(?,?,?,?)", (club_id, "DEPARTMENT_UPGRADED", context.current_date.isoformat(), f'{{"department":"{department}","level":{offer["target_level"]},"cost":{offer["cost"]}}}'))
        self._refresh_profile(club_id)
        return offer

    def process_weekly_costs(self, club_id: int, managed_transaction: bool = True) -> dict:
        profile = self._refresh_profile(club_id, managed_transaction=managed_transaction)
        context = self._context("weekly", str(club_id))
        total = profile.weekly_player_payroll + profile.weekly_staff_payroll + profile.weekly_department_maintenance
        existing = self.connection.execute("SELECT 1 FROM weekly_economy_runs WHERE club_id=? AND season=? AND week=?", (club_id, context.season, context.week)).fetchone()
        if existing:
            return {"processed": False, "weekly_cost": total, "reason": "ALREADY_PROCESSED"}
        state = self.connection.execute("SELECT cash FROM club_economic_state WHERE club_id=?", (club_id,)).fetchone()
        if state is None or int(state["cash"]) < total:
            raise DomainError(DomainErrorCode.INSUFFICIENT_CASH)
        with (self.connection if managed_transaction else nullcontext()):
            self.connection.execute("UPDATE club_economic_state SET cash=cash-?,expense_accumulated=expense_accumulated+?,updated_at=? WHERE club_id=?", (total, total, context.current_date.isoformat(), club_id))
            self.connection.execute("INSERT INTO weekly_economy_runs VALUES(?,?,?,?,?)", (club_id, context.season, context.week, total, context.current_date.isoformat()))
            self.ledger.post(context, club_id, "EXPENSE", "PLAYER_PAYROLL", -profile.weekly_player_payroll, "weekly_payroll", f"players:{club_id}", "Folha semanal do elenco")
            self.ledger.post(context, club_id, "EXPENSE", "STAFF_PAYROLL", -profile.weekly_staff_payroll, "weekly_payroll", f"staff:{club_id}", "Folha semanal da comissão")
            self.ledger.post(context, club_id, "EXPENSE", "DEPARTMENT_MAINTENANCE", -profile.weekly_department_maintenance, "weekly_payroll", f"departments:{club_id}", "Manutenção semanal de departamentos")
        return {"processed": True, "weekly_cost": total, "player_payroll": profile.weekly_player_payroll, "staff_payroll": profile.weekly_staff_payroll, "department_maintenance": profile.weekly_department_maintenance}

    def process_weekly_costs_all(self, managed_transaction: bool = True) -> dict:
        """Debita a semana corrente para todos os clubes já inicializados.

        Cada clube mantém seu lançamento idempotente por temporada e semana. A
        falta de caixa é reportada por clube, sem interromper o processamento do
        restante do mundo.
        """
        club_ids = [
            int(row["club_id"])
            for row in self.connection.execute(
                "SELECT club_id FROM club_payroll_profiles ORDER BY club_id"
            ).fetchall()
        ]
        processed = 0
        already_processed = 0
        insufficient_cash: list[int] = []
        for club_id in club_ids:
            try:
                result = self.process_weekly_costs(club_id, managed_transaction)
            except ValueError as error:
                if str(error) != "INSUFFICIENT_CASH":
                    raise
                insufficient_cash.append(club_id)
                continue
            if result["processed"]:
                processed += 1
            else:
                already_processed += 1
        return {
            "clubs_total": len(club_ids),
            "processed": processed,
            "already_processed": already_processed,
            "insufficient_cash_club_ids": insufficient_cash,
        }
