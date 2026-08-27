"""Contratos estruturais para módulos futuros; nenhum comportamento de jogo é executado aqui."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from enum import Enum


class StructuralStatus(str, Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class ScoutMission:
    scout_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    target_country: int | None = None
    target_competition: int | None = None
    status: StructuralStatus = StructuralStatus.PLANNED


@dataclass
class TransferWindow:
    season: str
    start_date: date | None = None
    end_date: date | None = None


@dataclass
class FinanceState:
    cash: int = 0
    revenue: int = 0
    expenses: int = 0
    debt: int = 0


@dataclass
class StaffMember:
    staff_id: int | None = None
    role: str = ""
    name: str = ""


@dataclass
class StadiumState:
    stadium_id: int | None = None
    capacity: int | None = None


@dataclass
class SponsorState:
    sponsor_id: int | None = None
    name: str = ""


class SimulationService:
    """Ponto de extensão; simulação deliberadamente não implementada."""
    def advance(self, *_args, **_kwargs):
        raise NotImplementedError("A simulação será implementada em etapa posterior.")
