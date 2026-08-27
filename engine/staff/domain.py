from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum
from datetime import date


class StaffRole(StrEnum):
    MANAGER = "treinador"
    ASSISTANT = "auxiliar"
    FITNESS_COACH = "preparador_fisico"
    DOCTOR = "medico"
    SCOUT = "scout"


class StaffStatus(StrEnum):
    ACTIVE = "ativo"
    AVAILABLE = "disponivel"
    RETIRED = "aposentado"


@dataclass
class StaffContract:
    contract_id: int | None = None
    salary: int = 0
    start_date: date | None = None
    end_date: date | None = None
    status: str = "ativo"


@dataclass
class StaffMember:
    staff_id: int | None
    name: str
    role: StaffRole
    age: int
    club_id: int | None = None
    career_start_age: int | None = None
    experience: int = 0
    reputation: int = 1
    level: int = 1
    potential: int = 50
    specialization: str | None = None
    salary: int = 0
    status: StaffStatus = StaffStatus.AVAILABLE
    retirement_age: int | None = None
    contract: StaffContract = field(default_factory=StaffContract)
    history: list[dict] = field(default_factory=list)

    def efficiency(self) -> float:
        return min(1.0, max(0.0, (self.level * 0.35 + self.experience * 0.35 + self.reputation * 0.30) / 100))


@dataclass
class ClubDepartment:
    club_id: int
    department: str
    level: int = 1
    cost: int = 0
    capacity: int = 0
    maintenance: int = 0
    efficiency: float = 0.0

    def normalized_efficiency(self) -> float:
        return min(1.0, max(0.0, self.efficiency if self.efficiency else self.level / 10))
