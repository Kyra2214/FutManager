from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from engine.staff.domain import StaffMember


@dataclass(frozen=True)
class ClubStrengthComponents:
    players: float
    staff: float
    infrastructure: float

    @property
    def total(self) -> float:
        return self.players + self.staff + self.infrastructure


class ClubStrengthService:
    """Agrega componentes sem definir resultado de partidas."""
    def calculate(self, players: Iterable[float], staff: Iterable[StaffMember], infrastructure: Iterable[float]) -> ClubStrengthComponents:
        p=list(players); s=list(staff); i=list(infrastructure)
        player_value=sum(max(0,min(99,x)) for x in p) / len(p) if p else 0.0
        staff_value=sum(x.efficiency()*100 for x in s) / len(s) if s else 0.0
        infra_value=sum(max(0,min(100,x)) for x in i) / len(i) if i else 0.0
        return ClubStrengthComponents(player_value, staff_value, infra_value)
