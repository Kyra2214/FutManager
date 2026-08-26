from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import random
import sqlite3
from contextlib import nullcontext

from engine.social.stadium_fans import SocialService
from engine.core.domain_errors import DomainError, DomainErrorCode

SCHEMA = """
CREATE TABLE IF NOT EXISTS ticket_price_configs (
  club_id INTEGER PRIMARY KEY,
  base_price INTEGER NOT NULL CHECK(base_price >= 1),
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS stadium_ticket_sectors(sector_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,name TEXT NOT NULL,capacity INTEGER NOT NULL CHECK(capacity > 0),price_multiplier REAL NOT NULL DEFAULT 1.0,UNIQUE(club_id,name));
CREATE TABLE IF NOT EXISTS ticket_sales(sale_id INTEGER PRIMARY KEY AUTOINCREMENT,match_id INTEGER NOT NULL,club_id INTEGER NOT NULL,sector_id INTEGER NOT NULL,quantity INTEGER NOT NULL CHECK(quantity > 0),unit_price INTEGER NOT NULL,complimentary INTEGER NOT NULL DEFAULT 0,reason TEXT NOT NULL DEFAULT '',responsible TEXT NOT NULL DEFAULT '',status TEXT NOT NULL DEFAULT 'SOLD',created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS ticket_refunds(refund_id INTEGER PRIMARY KEY AUTOINCREMENT,sale_id INTEGER NOT NULL UNIQUE,amount INTEGER NOT NULL,reason TEXT NOT NULL,created_at TEXT NOT NULL);
"""


@dataclass(frozen=True)
class AttendanceEstimate:
    expected: int
    actual: int
    capacity: int
    ticket_price: int
    demand: float


class AttendanceService:
    """Público de jogo derivado de dados sociais e de estádio, sem valor no frontend."""

    def __init__(self, database: str | sqlite3.Connection):
        if not isinstance(database, sqlite3.Connection):
            from engine.core.state_store import assert_mutable_state_path
            assert_mutable_state_path(database)
        self.connection = sqlite3.connect(database) if not isinstance(database, sqlite3.Connection) else database
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.executescript(SCHEMA)
        self.social = SocialService(self.connection)
        self.connection.commit()

    def configure_sector(self, club_id: int, name: str, capacity: int, price_multiplier: float = 1.0) -> dict:
        if int(capacity) <= 0 or float(price_multiplier) <= 0 or not str(name).strip(): raise ValueError('TICKET_SECTOR_INVALID')
        with self.connection:
            self.connection.execute('INSERT INTO stadium_ticket_sectors(club_id,name,capacity,price_multiplier) VALUES(?,?,?,?) ON CONFLICT(club_id,name) DO UPDATE SET capacity=excluded.capacity,price_multiplier=excluded.price_multiplier',(int(club_id),str(name).strip(),int(capacity),float(price_multiplier)))
        return dict(self.connection.execute('SELECT * FROM stadium_ticket_sectors WHERE club_id=? AND name=?',(int(club_id),str(name).strip())).fetchone())

    def preview_sector_demand(self, match_id: int, club_id: int) -> list[dict]:
        rows=[]
        for sector in self.connection.execute('SELECT * FROM stadium_ticket_sectors WHERE club_id=? ORDER BY sector_id',(int(club_id),)).fetchall():
            sold=self.connection.execute("SELECT COALESCE(SUM(quantity),0) FROM ticket_sales WHERE match_id=? AND sector_id=? AND status='SOLD'",(int(match_id),int(sector['sector_id']))).fetchone()[0]
            rows.append({'sector_id':int(sector['sector_id']),'name':sector['name'],'capacity':int(sector['capacity']),'sold':int(sold),'available':max(0,int(sector['capacity'])-int(sold)),'persisted':False})
        return rows

    def sell_tickets(self, match_id: int, club_id: int, sector_id: int, quantity: int, unit_price: int, complimentary: bool = False, reason: str = '', responsible: str = '') -> dict:
        if int(quantity) <= 0 or int(unit_price) < 0: raise ValueError('TICKET_SALE_INVALID')
        sector=self.connection.execute('SELECT * FROM stadium_ticket_sectors WHERE sector_id=? AND club_id=?',(int(sector_id),int(club_id))).fetchone()
        if not sector: raise KeyError(sector_id)
        available=self.preview_sector_demand(match_id,club_id); current=next((x for x in available if x['sector_id']==int(sector_id)),None)
        if not current or int(quantity)>current['available']: raise ValueError('TICKET_CAPACITY_EXCEEDED')
        if complimentary and (not str(reason).strip() or not str(responsible).strip()): raise ValueError('COMPLIMENTARY_AUDIT_REQUIRED')
        with self.connection:
            cur=self.connection.execute('INSERT INTO ticket_sales(match_id,club_id,sector_id,quantity,unit_price,complimentary,reason,responsible,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(int(match_id),int(club_id),int(sector_id),int(quantity),int(unit_price),int(bool(complimentary)),str(reason),str(responsible),date.today().isoformat()))
        return {'sale_id':int(cur.lastrowid),'quantity':int(quantity),'gross_revenue':0 if complimentary else int(quantity)*int(unit_price),'complimentary':bool(complimentary),'persisted':True}

    def refund_ticket_sale(self, sale_id: int, reason: str) -> dict:
        sale=self.connection.execute("SELECT * FROM ticket_sales WHERE sale_id=? AND status='SOLD'",(int(sale_id),)).fetchone()
        if not sale: raise KeyError(sale_id)
        amount=0 if sale['complimentary'] else int(sale['quantity'])*int(sale['unit_price'])
        with self.connection:
            self.connection.execute("UPDATE ticket_sales SET status='REFUNDED' WHERE sale_id=?",(int(sale_id),))
            self.connection.execute('INSERT INTO ticket_refunds(sale_id,amount,reason,created_at) VALUES(?,?,?,?)',(int(sale_id),amount,str(reason),date.today().isoformat()))
        return {'sale_id':int(sale_id),'refund':amount,'persisted':True}

    def occupancy(self, match_id: int, club_id: int) -> dict:
        rows=self.preview_sector_demand(match_id,club_id); return {'match_id':int(match_id),'club_id':int(club_id),'capacity':sum(x['capacity'] for x in rows),'sold':sum(x['sold'] for x in rows),'expected':sum(x['capacity'] for x in rows),'realized':sum(x['sold'] for x in rows),'sectors':rows}

    def configure_ticket_price(self, club_id: int, base_price: int) -> None:
        if base_price < 1 or base_price > 2_000:
            raise DomainError(DomainErrorCode.INVALID_TICKET_PRICE)
        with self.connection:
            self.connection.execute("INSERT INTO ticket_price_configs(club_id,base_price,updated_at) VALUES(?,?,?) ON CONFLICT(club_id) DO UPDATE SET base_price=excluded.base_price,updated_at=excluded.updated_at", (club_id, base_price, date.today().isoformat()))

    def _price(self, club_id: int, importance: int, competition_factor: float, demand: float) -> int:
        configured = self.connection.execute("SELECT base_price FROM ticket_price_configs WHERE club_id=?", (club_id,)).fetchone()
        base = int(configured["base_price"]) if configured else 35
        modifier = 1 + min(0.30, max(-0.15, (importance - 50) / 250)) + min(0.12, max(-0.08, (demand - 0.55) / 6))
        return max(1, int(round(base * competition_factor * modifier)))

    def estimate(self, match_id: int, home_club_id: int, away_club_id: int, importance: int = 50, competition_factor: float = 1.0, seed: int | None = None, managed_transaction: bool = True) -> AttendanceEstimate:
        existing = self.connection.execute("SELECT * FROM attendance_records WHERE match_id=?", (match_id,)).fetchone()
        if existing:
            capacity = self.connection.execute("SELECT usable_capacity FROM club_stadiums WHERE club_id=? AND is_primary=1", (home_club_id,)).fetchone()
            return AttendanceEstimate(int(existing["expected_attendance"]), int(existing["actual_attendance"]), int(capacity[0] if capacity else existing["actual_attendance"]), int(existing["ticket_price"]), float(existing["occupancy_rate"]))
        self.social.ensure_fan_reputation(home_club_id, managed_transaction=managed_transaction)
        self.social.ensure_fan_reputation(away_club_id, managed_transaction=managed_transaction)
        stadium = self.connection.execute("SELECT usable_capacity,comfort,security,quality FROM club_stadiums WHERE club_id=? AND is_primary=1 AND status='ACTIVE'", (home_club_id,)).fetchone()
        if not stadium:
            raise DomainError(DomainErrorCode.STADIUM_NOT_INITIALIZED)
        fan = self.connection.execute("SELECT * FROM club_fan_base WHERE club_id=?", (home_club_id,)).fetchone()
        home_rep = self.connection.execute("SELECT * FROM club_reputation WHERE club_id=?", (home_club_id,)).fetchone()
        away_rep = self.connection.execute("SELECT sporting,national FROM club_reputation WHERE club_id=?", (away_club_id,)).fetchone()
        capacity = max(1, int(stadium["usable_capacity"]))
        fan_pressure = min(1.35, max(0.05, int(fan["size"]) / capacity))
        social = (int(fan["satisfaction"]) * 0.35 + int(fan["engagement"]) * 0.20 + int(fan["interest"]) * 0.15 + int(home_rep["sporting"]) * 0.15 + int(home_rep["commercial"]) * 0.05 + int(stadium["comfort"]) * 0.05 + int(stadium["security"]) * 0.025 + int(stadium["quality"]) * 0.025) / 100
        opponent = ((int(away_rep["sporting"]) + int(away_rep["national"])) / 200) * 0.15
        demand = min(1.0, max(0.02, 0.12 + fan_pressure * 0.45 + social * 0.32 + opponent + max(0, min(100, importance)) / 1000))
        ticket_price = self._price(home_club_id, importance, competition_factor, demand)
        expected = max(0, min(capacity, int(round(capacity * demand))))
        rng = random.Random(seed if seed is not None else match_id)
        actual = max(0, min(capacity, int(round(expected * (0.96 + rng.random() * 0.08)))))
        with (self.connection if managed_transaction else nullcontext()):
            self.connection.execute("INSERT INTO attendance_records(match_id,club_id,expected_attendance,actual_attendance,occupancy_rate,ticket_price,revenue,seed) VALUES(?,?,?,?,?,?,?,?)", (match_id, home_club_id, expected, actual, actual / capacity, ticket_price, actual * ticket_price, seed if seed is not None else match_id))
        return AttendanceEstimate(expected, actual, capacity, ticket_price, demand)
