from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import random


@dataclass(frozen=True)
class CareerRulesConfig:
    starting_age: int = 16
    peak_start_age: int = 23
    peak_end_age: int = 30
    peak_target_age: int = 27
    decline_start_age: int = 31
    retirement_min_age: int = 35
    return_seasons_out: int = 1
    max_potential: int = 99
    min_potential: int = 1
    max_strength: int = 99
    min_strength: int = 1
    development_rate: float = 0.18
    decline_rate: float = 0.06


class CareerStatus(StrEnum):
    YOUTH = "YOUTH"
    ACTIVE = "ACTIVE"
    RETIRING = "RETIRING"
    RETIRED = "RETIRED"
    RETURNED = "RETURNED"


@dataclass(frozen=True)
class PotentialDistribution:
    low_weight: float = 0.45
    medium_weight: float = 0.30
    good_weight: float = 0.15
    star_weight: float = 0.07
    superstar_weight: float = 0.025
    phenomenon_weight: float = 0.005

    def sample(self, rng: random.Random, minimum: int = 1, maximum: int = 99) -> int:
        tiers = [(25, self.low_weight), (55, self.medium_weight), (75, self.good_weight), (88, self.star_weight), (96, self.superstar_weight), (99, self.phenomenon_weight)]
        value = rng.choices(tiers, weights=[x[1] for x in tiers])[0][0]
        lower = 1 if value == 25 else ({55:26,75:56,88:76,96:89,99:97}[value])
        return rng.randint(max(minimum, lower), min(maximum, value))


class PlayerRules:
    def __init__(self, config: CareerRulesConfig | None = None, distribution: PotentialDistribution | None = None):
        self.config = config or CareerRulesConfig()
        self.distribution = distribution or PotentialDistribution()

    def validate_new_age(self, age: int) -> None:
        if age != self.config.starting_age:
            raise ValueError(f"novos jogadores devem começar aos {self.config.starting_age} anos")

    def generate_potential(self, seed: int | None = None) -> int:
        rng = random.Random(seed)
        return self.distribution.sample(rng, self.config.min_potential, self.config.max_potential)

    def development_factor(self, age: int) -> float:
        if age < 16: return 0.0
        if age <= 22: return 0.55 + (age - 16) * 0.06
        if age <= 25: return 0.91 + (age - 22) * 0.025
        if age <= 30: return 0.985
        years = age - self.config.decline_start_age + 1
        return max(0.55, 1.0 - years * self.config.decline_rate)

    def calculate_strength(self, potential: int, age: int, development_factor: float | None = None) -> int:
        if not self.config.min_potential <= potential <= self.config.max_potential:
            raise ValueError("potential fora do intervalo configurado")
        factor = self.development_factor(age) if development_factor is None else development_factor
        strength = round(potential * factor)
        return max(self.config.min_strength, min(self.config.max_strength, min(potential, strength)))

    def next_status(self, age: int, current: CareerStatus, retirement_requested: bool = False) -> CareerStatus:
        if retirement_requested: return CareerStatus.RETIRED
        if current == CareerStatus.RETIRED: return CareerStatus.RETIRED
        if current == CareerStatus.YOUTH and age >= 18: return CareerStatus.ACTIVE
        if current in (CareerStatus.ACTIVE, CareerStatus.RETURNED) and age >= self.config.retirement_min_age: return CareerStatus.RETIRING
        return current

    def can_return(self, status: CareerStatus, seasons_out: int) -> bool:
        return status == CareerStatus.RETIRED and seasons_out >= self.config.return_seasons_out
